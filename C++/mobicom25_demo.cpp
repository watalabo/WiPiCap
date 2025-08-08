#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <cstring>
#include <bitset>
#include <thread>
#include <mutex>

#include <pcap.h>
#include <eigen3/Eigen/Dense>
#include "matplotlibcpp.h"

// Namespace alias
namespace plt = matplotlibcpp;
using namespace std;
using namespace Eigen;

// ====================== global variable ======================
mutex g_mtx;
MatrixXd g_latest_amp;  
MatrixXd g_latest_phase; 
bool g_v_updated = false;

// ====================== constant ======================
constexpr double PI = 3.14159265358979323846;


// ====================== helper function ======================

// Convert byte array to hexadecimal string
inline string to_hex_string(const u_char* data, int len) {
    static const char* hexmap = "0123456789abcdef";
    string hex(len * 2, '0');
    for (int i = 0; i < len; i++) {
        hex[2 * i] = hexmap[(data[i] >> 4) & 0xF];
        hex[2 * i + 1] = hexmap[data[i] & 0xF];
    }
    return hex;
}

// Flip hex string (Little Endian to Big Endian)
inline string hex_flip(const string& hex_str) {
    string flipped;
    flipped.reserve(hex_str.size());
    for (int i = hex_str.size() - 2; i >= 0; i -= 2)
        flipped.append(hex_str.substr(i, 2));
    return flipped;
}

// Convert quantized angle to radians
inline double quantized_angle(const string& type, int angle, int phi_size, int psi_size) {
    return (type == "phi")
        ? PI * angle / (1 << (phi_size - 1)) + PI / (1 << phi_size)
        : PI * angle / (1 << (psi_size + 1)) + PI / (1 << (psi_size + 2));
}

// Reconstruct V-matrix from Givens rotation
MatrixXcd inverse_givens_rotation(int nr, int nc,
                                  const vector<double>& angles,
                                  const vector<string>& angle_type,
                                  const vector<pair<int,int>>& angle_idx) {
    MatrixXcd mat_e = MatrixXcd::Identity(nr, nc);
    MatrixXcd d_li = MatrixXcd::Identity(nr, nr);
    MatrixXcd g_li = MatrixXcd::Identity(nr, nr);
    int d_count = 0, d_patience = 1;

    for (int k = (int)angles.size() - 1; k >= 0; k--) {
        const auto& t = angle_type[k];
        const auto& idx = angle_idx[k];

        if (t == "phi") {
            d_li(idx.first, idx.first) = exp(complex<double>(0, angles[k]));
            d_count++;
        } else {
            double c = cos(angles[k]);
            double s = sin(angles[k]);
            g_li(idx.second, idx.second) = c;
            g_li(idx.second, idx.first) = s;
            g_li(idx.first, idx.second) = -s;
            g_li(idx.first, idx.first) = c;
            mat_e = g_li.adjoint() * mat_e;
            g_li.setIdentity();
        }

        if (d_count == d_patience) {
            mat_e = d_li.adjoint() * mat_e;
            d_patience++;
            d_count = 0;
            d_li.setIdentity();
        }
    }
    return mat_e;
}

// Decode quantized angles
vector<int> decode_quantized_angles(const string& cbr_hex,
                                    int num_snr, int num_subc,
                                    int angle_seq_len,
                                    const vector<int>& angle_bits_order) {
    string cbr_bin;
    cbr_bin.reserve(cbr_hex.size() * 4);
    for (char c : cbr_hex) {
        int val = (c <= '9') ? c - '0' : 10 + (tolower(c) - 'a');
        cbr_bin += bitset<4>(val).to_string();
    }
    reverse(cbr_bin.begin(), cbr_bin.end());
    cbr_bin = cbr_bin.substr(num_snr * 8);

    vector<int> cbr_angles;
    if (angle_seq_len == 0) return cbr_angles;
    int max_length = num_subc * angle_seq_len;
    cbr_angles.reserve(max_length / 4);

    for (int i = 0; i < max_length; i += angle_seq_len) {
        int start = 0;
        for (size_t k = 1; k < angle_bits_order.size(); k++) {
             if (i + start + angle_bits_order[k] > cbr_bin.length()) continue;
            string seg = cbr_bin.substr(i + start, angle_bits_order[k]);
            if (seg.empty()) continue;
            cbr_angles.push_back(stoi(seg, nullptr, 2));
            start += angle_bits_order[k];
        }
    }
    return cbr_angles;
}

// ====================== packet parsing ======================
void process_cbr_packet(const u_char* packet, const struct pcap_pkthdr* header) {
    try {
        string raw_hex = to_hex_string(packet, header->len);
        int radiotap_len = packet[2] | (packet[3] << 8);

        int category_code_offset = radiotap_len + 24;
        if ((int)raw_hex.size() <= (category_code_offset + 1) * 2) return;
        
        int category_code = stoi(raw_hex.substr(category_code_offset * 2, 2), nullptr, 16);

        int mimo_control_offset = category_code_offset + 2;
        int nr, nc, codebook_info, phi_size, psi_size, mimo_control_len;
        
        if (category_code == 21) { /* VHT */
            mimo_control_len = 3;
            if((int)raw_hex.size() <= (mimo_control_offset + mimo_control_len) * 2) return;
            string bin_str = bitset<24>(stoul(hex_flip(raw_hex.substr(mimo_control_offset * 2, mimo_control_len * 2)), nullptr, 16)).to_string();
            codebook_info = bin_str[13] - '0';
            nr = stoi(bin_str.substr(18, 3), nullptr, 2) + 1;
            nc = stoi(bin_str.substr(21), nullptr, 2) + 1;
        } else if (category_code == 30) { /* HE */
            mimo_control_len = 5;
            if((int)raw_hex.size() <= (mimo_control_offset + mimo_control_len) * 2) return;
            string bin_str = bitset<40>(stoull(hex_flip(raw_hex.substr(mimo_control_offset * 2, mimo_control_len * 2)), nullptr, 16)).to_string();
            codebook_info = bin_str[30] - '0';
            nr = stoi(bin_str.substr(34, 3), nullptr, 2) + 1;
            nc = stoi(bin_str.substr(37), nullptr, 2) + 1;
        } else {
            return;
        }

        phi_size = (codebook_info == 0) ? 4 : 6;
        psi_size = (codebook_info == 0) ? 2 : 4;
        
        vector<int> angle_bits_order;
        vector<string> angle_type;
        vector<pair<int,int>> angle_index;
        pair<int,int> phi_idx = {0, 0}, psi_idx = {1, 0};
        int cnt = nr - 1;

        while ((int)angle_bits_order.size() < min(nc, nr-1) * (2*(nr-1) - min(nc, nr-1) + 1)) {
            for (int i = 0; i < cnt; i++) { angle_bits_order.push_back(phi_size); angle_type.push_back("phi"); angle_index.emplace_back(phi_idx.first + i, phi_idx.second); }
            phi_idx.first++; phi_idx.second++;
            for (int i = 0; i < cnt; i++) { angle_bits_order.push_back(psi_size); angle_type.push_back("psi"); angle_index.emplace_back(psi_idx.first + i, psi_idx.second); }
            psi_idx.first++; psi_idx.second++;
            cnt--;
        }

        int cbr_payload_offset = mimo_control_offset + mimo_control_len;
        string cbr_hex = hex_flip(raw_hex.substr(cbr_payload_offset * 2, raw_hex.size() - cbr_payload_offset * 2 - 8));
        
        int num_snr = nc;
        int phi_count = count(angle_type.begin(), angle_type.end(), "phi");
        int psi_count = count(angle_type.begin(), angle_type.end(), "psi");
        int denom = phi_size * phi_count + psi_size * psi_count;

        if (denom == 0) return;

        int num_subc = ((int)cbr_hex.size() - num_snr * 2) * 4 / denom;
        if (num_subc <= 0) return;
        
        int angle_seq_len = 0;
        for (auto b : angle_bits_order) angle_seq_len += b;

        vector<int> angle_dec = decode_quantized_angles(cbr_hex, num_snr, num_subc, angle_seq_len, angle_bits_order);

        int subc_len = angle_type.size() -1;
        if (subc_len <= 0 || (int)angle_dec.size() < num_subc * subc_len) return;

        MatrixXd amp_matrix(num_subc, nc);
        MatrixXd phase_matrix(num_subc, nc);

        for (int s = 0; s < num_subc; s++) {
            vector<double> angles;
            angles.reserve(subc_len);
            for (int k = 0; k < subc_len; k++) {
                angles.push_back(quantized_angle(angle_type[k+1], angle_dec[s * subc_len + k], phi_size, psi_size));
            }
            vector<pair<int,int>> sampled_angle_index(angle_index.begin() + 1, angle_index.end());
            vector<string> sampled_angle_type(angle_type.begin() + 1, angle_type.end());

            MatrixXcd v = inverse_givens_rotation(nr, nc, angles, sampled_angle_type, sampled_angle_index);
            
            for (int c = 0; c < nc; ++c) {
                amp_matrix(s, c) = abs(v(0, c));
                phase_matrix(s, c) = arg(v(0, c));
            }
        }

        lock_guard<mutex> guard(g_mtx);
        g_latest_amp = amp_matrix;
        g_latest_phase = phase_matrix;
        g_v_updated = true;

    } catch (...) { return; }
}

// ====================== pcap call back function ======================
void packet_handler(u_char* user, const struct pcap_pkthdr* header, const u_char* packet) {
    process_cbr_packet(packet, header);
}

// ====================== main function ======================
int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <interface> <target_mac>" << endl;
        cerr << "Example: sudo " << argv[0] << " mon0 82:3a:39:67:fe:84" << endl;
        return 1;
    }

    char* dev = argv[1]; 
    string target_mac_str = argv[2];
    
    string mac_no_colons = target_mac_str;
    mac_no_colons.erase(remove(mac_no_colons.begin(), mac_no_colons.end(), ':'), mac_no_colons.end());

    if (mac_no_colons.length() != 12) {
        cerr << "Invalid MAC address format. Please use xx:xx:xx:xx:xx:xx" << endl;
        return 1;
    }

    string mac_part1 = mac_no_colons.substr(0, 8);
    string mac_part2 = mac_no_colons.substr(8, 4);

    string filter_exp = "wlan[10:4] == 0x" + mac_part1 + " and wlan[14:2] == 0x" + mac_part2;
    
    char errbuf[PCAP_ERRBUF_SIZE];
    cout << "Capturing on device: " << dev << endl;
    cout << "Using filter: " << filter_exp << endl; 
    
    pcap_t* handle = pcap_open_live(dev, BUFSIZ, 1, 1000, errbuf);
    if (handle == NULL) {
        cerr << "Couldn't open device " << dev << ": " << errbuf << endl;
        return 2;
    }
    

    struct bpf_program fp;
    if (pcap_compile(handle, &fp, filter_exp.c_str(), 0, PCAP_NETMASK_UNKNOWN) == -1) {
        cerr << "Couldn't compile filter '" << filter_exp << "': " << pcap_geterr(handle) << endl;
        return 2;
    }
    if (pcap_setfilter(handle, &fp) == -1) {
        cerr << "Couldn't install filter '" << filter_exp << "': " << pcap_geterr(handle) << endl;
        return 2;
    }
    
    thread pcap_thread([&handle]() {
        pcap_loop(handle, -1, packet_handler, NULL);
    });

    cout << "Starting real-time V-matrix visualization..." << endl;

    while (true) {
        bool updated;
        MatrixXd current_amp, current_phase;
        {
            lock_guard<mutex> guard(g_mtx);
            updated = g_v_updated;
            if (updated) {
                current_amp = g_latest_amp;
                current_phase = g_latest_phase;
                g_v_updated = false;
            }
        }
        
        if (updated) {
            plt::clf(); 

            plt::subplot(2, 1, 1); 
            vector<double> x_sampled;
            vector<vector<double>> y_amp_sampled(current_amp.cols());

            for (int i = 0; i < current_amp.rows(); i += 40) {
                x_sampled.push_back(i);
                for (int c = 0; c < current_amp.cols(); ++c) {
                    y_amp_sampled[c].push_back(current_amp(i, c));
                }
            }
            
            for(size_t c = 0; c < y_amp_sampled.size(); ++c) { // FIX: int -> size_t
                plt::plot(x_sampled, y_amp_sampled[c], {{"label", "Stream " + to_string(c)}});
            }
            plt::title("Amplitude vs. Subcarrier");
            plt::ylabel("Amplitude");
            plt::ylim(0.0, 1.5); // FIX: int -> double
            plt::legend();

            plt::subplot(2, 1, 2);
            vector<vector<double>> y_phase_sampled(current_phase.cols());
            for (int i = 0; i < current_phase.rows(); i += 40) {
                for (int c = 0; c < current_phase.cols(); ++c) {
                    y_phase_sampled[c].push_back(current_phase(i, c));
                }
            }

            for(size_t c = 0; c < y_phase_sampled.size(); ++c) { // FIX: int -> size_t
                plt::plot(x_sampled, y_phase_sampled[c], {{"label", "Stream " + to_string(c)}});
            }
            plt::title("Phase vs. Subcarrier");
            plt::xlabel("Subcarrier Index (Sampled every 40)");
            plt::ylabel("Phase (radians)");
            plt::ylim(-PI, PI); 
            plt::legend();
        }
        plt::pause(0.05); 
    }

    pcap_thread.join();
    pcap_close(handle);
    return 0;
}
