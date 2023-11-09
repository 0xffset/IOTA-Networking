#include <iostream>
#include <vector>
#include <unordered_set>
#include "single_include/nlohmann/json.hpp"
#include "./httplib.h"
#include "tangle.cpp"

using namespace std;

using namespace httplib;

using jso_nlohmann = nlohmann::json;

// Initialize the Blockchain
Tangle tangle;

string node_identifier = "YOUR_UNIQUE_NODE_IDENTIFIER"; // Replace with your unique node identifier

void resolve_conflicts() {
    // update tangle
    tangle.resolve_conflicts();
}

void new_transaction(const Request& req, Response& res) {
    // update tangle
    resolve_conflicts();

    // begin transaction
    jso_nlohmann values = jso_nlohmann::parse(req.body);

    // Check that the required fields are in the POST data
    if (!values.contains("sender") || !values.contains("recipient") || !values.contains("amount")) {
        res.status = 400;
        res.set_content("Missing values", "text/plain");
        return;
    }

    // Create a new Transaction
    int index = tangle.send_transaction(values);

    jso_nlohmann response = {{"message", "Transaction will be added to Block " + to_string(index)}};

    // tell peers to update tangle
    for (const auto& peer : tangle.peers) {
        auto response = Client((string("http://") + peer + "/peers/resolve").c_str());
    }

    res.set_content(response.dump(), "application/json");
}

void full_chain(const Request& req, Response& res) {
    jso_nlohmann response = {{"tangle", tangle.nodes}, {"length", tangle.nodes.size()}};
    res.set_content(response.dump(), "application/json");
}

void register_nodes(const Request& req, Response& res) {
    jso_nlohmann values = jso_nlohmann::parse(req.body);
    auto peers = values["peers"];

    if (peers.is_null()) {
        res.status = 400;
        res.set_content("Error: Please supply a valid list of nodes", "text/plain");
        return;
    }

    for (const auto& peer : peers) {
        tangle.register_peer(peer);
    }

    jso_nlohmann response = {{"message", "New peers have been added"}, {"total_nodes", tangle.peers}};

    res.set_content(response.dump(), "application/json");
}

void consensus(const Request& req, Response& res) {
    bool replaced = tangle.resolve_conflicts();

    jso_nlohmann response;
    if (replaced) {
        response = {{"message", "Our chain was replaced"}, {"new_chain", tangle.nodes}};
    } else {
        response = {{"message", "Our chain is authoritative"}, {"chain", tangle.nodes}};
    }

    res.set_content(response.dump(), "application/json");
}

void list_peers(const Request& req, Response& res) {
    jso_nlohmann response = {{"know_peers", tangle.peers}};
    res.set_content(response.dump(), "application/json");
}

int main() {
    Server app;

    app.Post("/transactions/new", new_transaction);
    app.Get("/tangle", full_chain);
    app.Post("/peers/register", register_nodes);
    app.Get("/peers/resolve", consensus);
    app.Get("/peers", list_peers);

    app.listen("0.0.0.0", 5001);

    return 0;
}
