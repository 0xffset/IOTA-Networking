#include <iostream>
#include <vector>
#include <set>
#include <ctime>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <random>
#include <openssl/sha.h>
#include "./httplib.h"
#include "single_include/nlohmann/json.hpp"

namespace json = nlohmann;

class Tangle {
public:
    std::vector<json::json> nodes;
    std::set<std::string> peers;

    bool valid_proof(int last_proof, const std::string& last_hash, int proof) {
        std::string guess = std::to_string(last_proof) + last_hash + std::to_string(proof);
        std::string guess_hash = sha256(guess);
        return guess_hash.substr(0, 4) == "0000";
    }

    int proof_of_work(int last_proof, const std::string& last_hash) {
        int proof = 0;
        while (!valid_proof(last_proof, last_hash, proof)) {
            proof++;
        }
        return proof;
    }

    std::string sha256(const std::string& input) {
        unsigned char hash[SHA256_DIGEST_LENGTH];
        SHA256_CTX sha256;
        SHA256_Init(&sha256);
        SHA256_Update(&sha256, input.c_str(), input.length());
        SHA256_Final(hash, &sha256);
        std::stringstream ss;
        for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
            ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
        }
        return ss.str();
    }

    void validate_node(json::json& node) {
        if (nodes[node["index"]]["validity"] < 1) {
            int last_proof = nodes[node["index"]]["proof"];
            std::string last_hash;
            for (const auto& prev_hash : nodes[node["index"]]["previous_hashs"]) {
                last_hash += prev_hash;
            }
            nodes[node["index"]]["proof"] = proof_of_work(last_proof, last_hash);
            nodes[node["index"]]["validity"] += 1;
        }
    }

    json::json create_node(const json::json& data, const std::vector<int>& prev_nodes, int new_index, int validity = 0) {
        std::vector<std::string> prev_hashes;

        for (int i : prev_nodes) {
            prev_hashes.push_back(sha256(nodes[i].dump()));
            nodes[i]["next_nodes"].push_back(new_index);
        }

        json::json node = {
            {"index", new_index},
            {"timestamp", std::time(0)},
            {"data", data},
            {"proof", 0},
            {"previous_hashs", prev_hashes},
            {"previous_nodes", prev_nodes},
            {"next_nodes", json::json::array()},
            {"validity", validity},
        };

        return node;
    }

    int send_transaction(const json::json& data) {
        std::vector<json::json> node_to_attach;
        std::vector<int> nodes_indexes;
        int new_index = nodes.size();
        std::vector<json::json> worst_cases_scenario;
        std::vector<int> worst_cases_scenario_indexes;

        for (int i = nodes.size() - 1; i >= 0; --i) {
            auto& node = nodes[i];
            if (node["validity"] < 1) {
                node_to_attach.push_back(node);
                nodes_indexes.push_back(node["index"]);
            } else {
                if (worst_cases_scenario.empty() || worst_cases_scenario.size() < 2) {
                    worst_cases_scenario.push_back(node);
                    worst_cases_scenario_indexes.push_back(node["index"]);
                }
            }
            if (node_to_attach.size() == 2) {
                break;
            }
        }

        while (node_to_attach.size() < 2) {
            node_to_attach.push_back(worst_cases_scenario.back());
            nodes_indexes.push_back(worst_cases_scenario_indexes.back());
            worst_cases_scenario.pop_back();
            worst_cases_scenario_indexes.pop_back();
        }

        for (auto& node : node_to_attach) {
            validate_node(node);
        }

        nodes.push_back(create_node(data, nodes_indexes, new_index));
        return new_index;
    }

    bool valid_tangle(const json::json& tangle) {
        for (const auto& node : tangle) {
            if (node["index"] >= 1) {
                int validity_of_node = node["validity"];
                auto next_nodes = node["next_nodes"];
                if (validity_of_node < next_nodes.size()) {
                    return false;
                }
                for (int n_node : next_nodes) {
                    if (node["index"] != nodes[n_node]["previous_nodes"]) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

public:
    Tangle() {
        for (int i = 0; i < 2; ++i) {
            nodes.push_back(create_node(nullptr, {}, nodes.size(), 1));
        }
    }

    bool resolve_conflicts() {
        std::set<std::string> neighbours = peers;
        json::json new_tangle = nullptr;
        size_t max_length = nodes.size();

        for (const auto& peer : neighbours) {
            httplib::Client client(peer.c_str());
            auto res = client.Get("/tangle");
            if (res && res->status == 200) {
                size_t length = res->get_header_value<size_t>("Content-Length").value_or(0);
                auto tangle = json::json::parse(res->body);

                if (length > max_length && valid_tangle(tangle)) {
                    max_length = length;
                    new_tangle = tangle;
                }
            }
        }

        if (new_tangle != nullptr) {
            nodes = new_tangle;
            return true;
        }
        return false;
    }

    void register_peer(const std::string& address) {
        peers.insert(address);
    }
};
