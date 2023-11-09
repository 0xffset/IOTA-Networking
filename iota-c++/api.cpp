#include <iostream>
#include <vector>
#include <unordered_set>
#include "single_include/nlohmann/json.hpp"
#include <cpphttplib/http_server.h>
#include "tangle.h" // assuming Tangle class is implemented in a separate header file

using namespace std;
using namespace httplib;

using json = nlohmann::json;

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
    json values = json::parse(req.body);

    // Check that the required fields are in the POST data
    if (!values.contains("sender") || !values.contains("recipient") || !values.contains("amount")) {
        res.status = 400;
        res.set_content("Missing values", "text/plain");
        return;
    }

    // Create a new Transaction
    int index = tangle.send_transaction(values);

    json response = {{"message", "Transaction will be added to Block " + to_string(index)}};

    // tell peers to update tangle
    for (const auto& peer : tangle.peers) {
        auto response = client.Get((string("http://") + peer + "/peers/resolve").c_str());
    }

    res.set_content(response.dump(), "application/json");
}

void full_chain(const Request& req, Response& res) {
    json response = {{"tangle", tangle.nodes}, {"length", tangle.nodes.size()}};
    res.set_content(response.dump(), "application/json");
}

void register_nodes(const Request& req, Response& res) {
    json values = json::parse(req.body);
    auto peers = values["peers"];

    if (peers.is_null()) {
        res.status = 400;
        res.set_content("Error: Please supply a valid list of nodes", "text/plain");
        return;
    }

    for (const auto& peer : peers) {
        tangle.register_peer(peer);
    }

    json response = {{"message", "New peers have been added"}, {"total_nodes", tangle.peers}};

    res.set_content(response.dump(), "application/json");
}

void consensus(const Request& req, Response& res) {
    bool replaced = tangle.resolve_conflicts();

    json response;
    if (replaced) {
        response = {{"message", "Our chain was replaced"}, {"new_chain", tangle.nodes}};
    } else {
        response = {{"message", "Our chain is authoritative"}, {"chain", tangle.nodes}};
    }

    res.set_content(response.dump(), "application/json");
}

void list_peers(const Request& req, Response& res) {
    json response = {{"know_peers", tangle.peers}};
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
