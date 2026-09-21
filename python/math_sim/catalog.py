from __future__ import annotations

from math_sim.registry import DemoDescriptor, Subcategory, create_default_registry


SUBCATEGORIES = (
    Subcategory("numerical", "math", "数値計算", order=10),
    Subcategory("structures", "math", "構造・生成", order=20),
    Subcategory("machine_learning", "information", "機械学習", order=10),
    Subcategory("algorithms", "information", "アルゴリズム", order=20),
    Subcategory("human_body", "biology", "人体", order=10),
)


DEMOS = (
    DemoDescriptor(
        "monte_carlo",
        "Monte Carlo Integral",
        "monte_carlo",
        "math",
        "numerical",
        description="乱数標本から定積分を推定します。",
        order=10,
        tags=("モンテカルロ", "積分", "確率"),
        aliases=("Monte Carlo",),
    ),
    DemoDescriptor(
        "random_tree",
        "Random Tree",
        "random_tree",
        "math",
        "structures",
        description="再帰的な分岐規則からランダムな木構造を生成します。",
        order=20,
        tags=("再帰", "木", "確率"),
    ),
    DemoDescriptor(
        "perceptron",
        "Perceptron",
        "perceptron",
        "information",
        "machine_learning",
        description="単一パーセプトロンの学習と論理ゲートを観察します。",
        order=10,
        tags=("AI", "機械学習", "分類"),
        related_subjects=("math",),
    ),
    DemoDescriptor(
        "mlp",
        "Multilayer Perceptron",
        "mlp",
        "information",
        "machine_learning",
        description="多層ニューラルネットワークの学習を観察します。",
        order=20,
        tags=("AI", "ニューラルネットワーク", "誤差逆伝播"),
        related_subjects=("math",),
    ),
    DemoDescriptor(
        "pathfinding",
        "Path Finding",
        "pathfinding",
        "information",
        "algorithms",
        description="複数の経路探索アルゴリズムを比較します。",
        order=30,
        tags=("A*", "BFS", "Dijkstra", "探索"),
        related_subjects=("math",),
    ),
    DemoDescriptor(
        "maze",
        "Maze Lab",
        "maze",
        "information",
        "algorithms",
        description="迷路生成と探索アルゴリズムを可視化します。",
        order=40,
        tags=("迷路", "探索", "生成"),
    ),
    DemoDescriptor(
        "maze_generator_race",
        "Generator Race",
        "maze_generator_race",
        "information",
        "algorithms",
        description="同じ条件で複数の迷路生成法を比較します。",
        order=50,
        tags=("迷路", "生成アルゴリズム", "比較"),
    ),
)


REGISTRY = create_default_registry(subcategories=SUBCATEGORIES, demos=DEMOS)
