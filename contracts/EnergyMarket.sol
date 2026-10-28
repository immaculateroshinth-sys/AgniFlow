// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Minimal educational order registry for AgniFlowZ.
/// It records sell orders and lets a buyer mark an order as purchased.
/// This starter does NOT transfer AGNI tokens or settle payments.
contract EnergyMarket {
    struct Order {
        address seller;
        uint256 energyKWh;       // stored in milli-kWh
        uint256 pricePerKWh;     // stored in milli-AGNI
        bool active;
    }

    mapping(uint256 => Order) public orders;
    uint256 public orderCount;

    event SellOrderCreated(uint256 indexed orderId, address indexed seller, uint256 energyKWh, uint256 pricePerKWh);
    event EnergyPurchased(uint256 indexed orderId, address indexed buyer);

    function createSellOrder(uint256 energyKWh, uint256 pricePerKWh) external returns (uint256 orderId) {
        require(energyKWh > 0, "Energy must be > 0");
        require(pricePerKWh > 0, "Price must be > 0");
        orderId = orderCount++;
        orders[orderId] = Order(msg.sender, energyKWh, pricePerKWh, true);
        emit SellOrderCreated(orderId, msg.sender, energyKWh, pricePerKWh);
    }

    function buyEnergy(uint256 orderId) external {
        Order storage order = orders[orderId];
        require(order.active, "Order not active");
        require(order.seller != msg.sender, "Seller cannot buy own order");
        order.active = false;
        emit EnergyPurchased(orderId, msg.sender);
    }
}
