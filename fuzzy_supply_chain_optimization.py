"""
Multi-Echelon Supply Chain Cost Optimization & Network Visualization
Author: Viktoriia Sobolta
"""

import numpy as np
from scipy.optimize import linprog
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def defuzzify_triangle(a: float, b: float, c: float) -> float:
    return (a + b + c) / 3.0


def plot_supply_chain_network(
    supply: list[float],
    demand: list[float],
    dc_capacity: list[float],
    allocation: np.ndarray,
    selected_routes: list[list[str]],
    total_cost: float,
    save_path: str = "optimal_network_map.png",
) -> None:
    """Draws a clean 3-tier supply chain flow diagram matching the optimization plan."""
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=150)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(-0.6, 4.6)
    ax.axis("off")

    # Node coordinates: Warehouses (x=0), DCs (x=1), Customers (x=2)
    pos_a = [(0.0, 3.3), (0.0, 2.0), (0.0, 0.7)]
    pos_d = [(1.0, 2.65), (1.0, 1.35)]
    pos_b = [(2.0, 4.0), (2.0, 3.0), (2.0, 2.0), (2.0, 1.0), (2.0, 0.0)]

    # Aggregate flows through Distribution Centers (D1, D2)
    flow_a_to_d = np.zeros((3, 2))
    flow_d_to_b = np.zeros((2, 5))
    direct_flows = []

    for i in range(3):
        for k in range(5):
            qty = allocation[i, k]
            if qty > 1e-6:
                route = selected_routes[i][k]
                if route == "Direct":
                    direct_flows.append((i, k, qty))
                elif route == "D1":
                    flow_a_to_d[i, 0] += qty
                    flow_d_to_b[0, k] += qty
                elif route == "D2":
                    flow_a_to_d[i, 1] += qty
                    flow_d_to_b[1, k] += qty

    # Helper to draw labeled arrows
    def draw_flow_arrow(start, end, label, color="#2b5c8f", rad=0.0, label_pos=0.45):
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops=dict(
                arrowstyle="-|>,head_length=0.7,head_width=0.4",
                color=color,
                lw=2.0,
                connectionstyle=f"arc3,rad={rad}",
                shrinkA=24,
                shrinkB=24,
            ),
            zorder=2,
        )
        # Calculate midpoint with slight arc offset for text label
        mx = start[0] + (end[0] - start[0]) * label_pos
        my = start[1] + (end[1] - start[1]) * label_pos - rad * 0.65
        ax.text(
            mx,
            my,
            label,
            fontsize=8.5,
            fontweight="bold",
            color=color,
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=0.8, alpha=0.95),
            zorder=4,
        )

    # 1. Draw Warehouse -> DC arrows
    for i in range(3):
        for j in range(2):
            if flow_a_to_d[i, j] > 1e-6:
                draw_flow_arrow(
                    pos_a[i],
                    pos_d[j],
                    f"{flow_a_to_d[i, j]:.0f} kg",
                    color="#1f4e78",
                    label_pos=0.48,
                )

    # 2. Draw DC -> Customer arrows
    for j in range(2):
        for k in range(5):
            if flow_d_to_b[j, k] > 1e-6:
                draw_flow_arrow(
                    pos_d[j],
                    pos_b[k],
                    f"{flow_d_to_b[j, k]:.0f} kg",
                    color="#2e75b6",
                    label_pos=0.52,
                )

    # 3. Draw Direct Shipment arrows (curved around hubs so they don't overlap D1/D2)
    for i, k, qty in direct_flows:
        arc_rad = -0.22 if i == 0 else 0.22
        draw_flow_arrow(
            pos_a[i],
            pos_b[k],
            f"Direct: {qty:.0f} kg",
            color="#d95f02",
            rad=arc_rad,
            label_pos=0.50,
        )

    # Helper to draw rectangular nodes
    def draw_node(center, title, subtitle, bg_color, border_color):
        w, h = 0.34, 0.44
        rect = patches.FancyBboxPatch(
            (center[0] - w / 2, center[1] - h / 2),
            w,
            h,
            boxstyle="round,pad=0.03,rounding_size=0.04",
            facecolor=bg_color,
            edgecolor=border_color,
            linewidth=1.8,
            zorder=3,
        )
        ax.add_patch(rect)
        ax.text(center[0], center[1] + 0.06, title, fontsize=11, fontweight="bold", ha="center", va="center", zorder=5)
        ax.text(center[0], center[1] - 0.11, subtitle, fontsize=8, color="#333333", ha="center", va="center", zorder=5)

    # Draw Warehouses (A)
    for i, p in enumerate(pos_a):
        draw_node(p, f"$A_{i+1}$", f"Supply: {supply[i]:.0f} kg", "#eef5fc", "#1f4e78")

    # Draw Distribution Centers (D)
    for j, p in enumerate(pos_d):
        used = flow_a_to_d[:, j].sum()
        draw_node(p, f"$D_{j+1}$", f"{used:.0f} / {dc_capacity[j]:.0f} kg", "#fff4e5", "#d95f02")

    # Draw Customers (B)
    for k, p in enumerate(pos_b):
        draw_node(p, f"$B_{k+1}$", f"Demand: {demand[k]:.0f} kg", "#edf7ed", "#2e7d32")

    # Column headers & title
    ax.text(0.0, 4.45, "Warehouses (Supply)", fontsize=11, fontweight="bold", ha="center", color="#1f4e78")
    ax.text(1.0, 4.45, "Distribution Hubs", fontsize=11, fontweight="bold", ha="center", color="#d95f02")
    ax.text(2.0, 4.45, "Customers (Demand)", fontsize=11, fontweight="bold", ha="center", color="#2e7d32")

    plt.title(
        f"Optimal Multi-Echelon Supply Chain Allocation Plan\nMinimum Total Transportation Cost: ${total_cost:,.2f}",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.show()


def main() -> None:
    supply = [
        defuzzify_triangle(950, 1000, 1050),
        defuzzify_triangle(1400, 1500, 1600),
        defuzzify_triangle(1100, 1200, 1300),
    ]

    demand = [
        defuzzify_triangle(850, 900, 950),
        defuzzify_triangle(630, 680, 730),
        defuzzify_triangle(950, 1000, 1050),
        defuzzify_triangle(450, 500, 550),
        defuzzify_triangle(570, 620, 670),
    ]

    cost_supply_to_dc = [
        [defuzzify_triangle(1.0, 2.0, 3.0), defuzzify_triangle(6.8, 8.0, 8.6)],
        [defuzzify_triangle(1.0, 3.0, 5.0), defuzzify_triangle(4.2, 5.0, 5.5)],
        [defuzzify_triangle(0.65, 1.05, 1.2), defuzzify_triangle(3.5, 4.0, 4.4)],
    ]

    cost_dc_to_demand = [
        [
            defuzzify_triangle(1.0, 2.5, 3.0),
            defuzzify_triangle(3.0, 4.5, 5.0),
            defuzzify_triangle(6.0, 7.5, 8.0),
            defuzzify_triangle(4.0, 5.5, 6.0),
            defuzzify_triangle(3.0, 4.5, 5.0),
        ],
        [
            defuzzify_triangle(2.0, 3.5, 4.0),
            defuzzify_triangle(3.0, 4.5, 5.0),
            defuzzify_triangle(4.0, 5.5, 6.0),
            defuzzify_triangle(3.0, 4.5, 5.0),
            defuzzify_triangle(2.0, 3.5, 4.0),
        ],
    ]

    direct_cost = [
        [0, defuzzify_triangle(1.5, 3.2, 4.5), 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, defuzzify_triangle(2.0, 4.5, 6.0), 0],
    ]

    big_m = 1e3
    cost_matrix = []
    selected_routes = []

    for i in range(len(cost_supply_to_dc)):
        row = []
        route_row = []
        for k in range(len(demand)):
            cost_d1 = cost_supply_to_dc[i][0] + cost_dc_to_demand[0][k]
            cost_d2 = cost_supply_to_dc[i][1] + cost_dc_to_demand[1][k]

            if direct_cost[i][k] > 0:
                direct_val = direct_cost[i][k]
                min_cost = min(direct_val, cost_d1, cost_d2)
                row.append(min_cost)
                route_row.append("Direct" if min_cost == direct_val else ("D1" if min_cost == cost_d1 else "D2"))
            else:
                min_cost = big_m
                best_dc = None
                for j in range(2):
                    path_cost = cost_supply_to_dc[i][j] + cost_dc_to_demand[j][k]
                    if path_cost < min_cost:
                        min_cost = path_cost
                        best_dc = f"D{j + 1}"
                row.append(min_cost)
                route_row.append(best_dc)

        cost_matrix.append(row)
        selected_routes.append(route_row)

    c_objective = np.array(cost_matrix).flatten()

    dc_capacity = [
        defuzzify_triangle(2400, 2500, 2600),
        defuzzify_triangle(1100, 1200, 1300),
    ]

    num_supply = len(supply)
    num_demand = len(demand)
    num_vars = num_supply * num_demand

    supply_constraints = np.zeros((num_supply, num_vars))
    for i in range(num_supply):
        for k in range(num_demand):
            supply_constraints[i, i * num_demand + k] = 1

    demand_constraints = np.zeros((num_demand, num_vars))
    for k in range(num_demand):
        for i in range(num_supply):
            demand_constraints[k, i * num_demand + k] = 1

    dc_capacity_constraints = np.zeros((2, num_vars))
    for k in range(num_demand):
        for i in range(num_supply):
            if selected_routes[i][k] == "D1":
                dc_capacity_constraints[0, i * num_demand + k] = 1
            elif selected_routes[i][k] == "D2":
                dc_capacity_constraints[1, i * num_demand + k] = 1

    A_eq = np.vstack([supply_constraints, demand_constraints])
    b_eq = np.hstack([supply, demand])
    A_ub = dc_capacity_constraints
    b_ub = dc_capacity

    result = linprog(
        c=c_objective,
        A_eq=A_eq,
        b_eq=b_eq,
        A_ub=A_ub,
        b_ub=b_ub,
        bounds=(0, None),
        method="highs",
    )

    if result.success:
        print(f"\nMinimum Total Transportation Cost: ${result.fun:,.2f}")
        allocation = result.x.reshape((num_supply, num_demand))
        for i in range(num_supply):
            for k in range(num_demand):
                if allocation[i, k] > 1e-6:
                    route = selected_routes[i][k]
                    print(f"  A{i+1} -> {route} -> B{k+1}: {allocation[i, k]:,.0f} kg")

        plot_supply_chain_network(supply, demand, dc_capacity, allocation, selected_routes, result.fun)
    else:
        print("Optimization failed:", result.message)


if __name__ == "__main__":
    main()
