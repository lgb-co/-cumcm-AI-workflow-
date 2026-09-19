import numpy as np
from scipy.stats import norm

# 参数设置
num_generations = 1000
population_size = 50
mutation_rate = 0.1
initial_temperature = 1000
cooling_rate = 0.995
sample_range = (10, 100)
threshold_range = (1, 10)
p0 = 0.10
confidence_level_reject = 0.95
confidence_level_accept = 0.90
alpha_reject = 1 - confidence_level_reject
alpha_accept = confidence_level_accept


def fitness(n, c, scenario):
    SE = np.sqrt(p0 * (1 - p0) / n)
    P_reject = 1 - norm.cdf((c - p0) / SE)
    P_accept = norm.cdf((c - p0) / SE)

    if scenario == 1:  # 确保拒收误差符合 95% 的信度
        reject_error = abs(P_reject - alpha_reject)
        return reject_error
    elif scenario == 2:  # 确保接收误差符合 90% 的信度
        accept_error = abs(P_accept - alpha_accept)
        return accept_error
    else:
        return np.inf  # 无效情景


def create_individual():
    n = np.random.randint(*sample_range)
    c = np.random.uniform(*threshold_range)
    return (n, c)


def mutate(individual):
    n, c = individual
    if np.random.rand() < 0.5:
        n = np.random.randint(*sample_range)
    else:
        c = np.random.uniform(*threshold_range)
    return (n, c)


def crossover(parent1, parent2):
    n1, c1 = parent1
    n2, c2 = parent2
    return (n1, c2) if np.random.rand() < 0.5 else (n2, c1)


def genetic_simulated_annealing(scenario):
    # 初始化种群
    population = [create_individual() for _ in range(population_size)]

    temperature = initial_temperature
    best_individual = min(population, key=lambda ind: fitness(*ind, scenario))

    for generation in range(num_generations):
        # 选择
        sorted_population = sorted(population, key=lambda ind: fitness(*ind, scenario))
        population = sorted_population[:population_size // 2]  # 选择前一半作为父母

        # 生成新个体
        offspring = []
        while len(offspring) < population_size:
            parents = np.random.choice(len(population), 2, replace=False)  # 选择索引
            parent1 = population[parents[0]]
            parent2 = population[parents[1]]
            child = crossover(parent1, parent2)
            if np.random.rand() < mutation_rate:
                child = mutate(child)
            offspring.append(child)

        population = population + offspring
        temperature *= cooling_rate

        # 找到当前最优个体
        current_best = min(population, key=lambda ind: fitness(*ind, scenario))
        if fitness(*current_best, scenario) < fitness(*best_individual, scenario):
            best_individual = current_best

        # 模拟退火：接受较差解的概率
        for ind in population:
            if np.random.rand() < np.exp(-fitness(*ind, scenario) / temperature):
                if fitness(*ind, scenario) < fitness(*best_individual, scenario):
                    best_individual = ind

    return best_individual


# 处理情况 1 - 在 95% 的信度下拒收次品率超过标称值
best_individual_scenario_1 = genetic_simulated_annealing(scenario=1)
best_n_1, best_c_1 = best_individual_scenario_1
print(f"情况 1 - 在 95% 的信度下拒收次品率超过标称值:")
print(f"最优样本量 n: {best_n_1:.2f}")
print(f"最优阈值 c: {best_c_1:.4f}")

# 处理情况 2 - 在 90% 的信度下接收次品率不超过标称值
best_individual_scenario_2 = genetic_simulated_annealing(scenario=2)
best_n_2, best_c_2 = best_individual_scenario_2
print(f"\n情况 2 - 在 90% 的信度下接收次品率不超过标称值:")
print(f"最优样本量 n: {best_n_2:.2f}")
print(f"最优阈值 c: {best_c_2:.4f}")
