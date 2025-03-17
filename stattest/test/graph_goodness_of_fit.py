from abc import ABC

from numpy import float64
from typing_extensions import override

from stattest.test.goodness_of_fit import AbstractGoodnessOfFitTestStatistic


class AbstractGraphTestStatistic(AbstractGoodnessOfFitTestStatistic, ABC):
    @override
    def execute_statistic(self, rvs, **kwargs) -> float | float64:
        dist = self._compute_dist(rvs)

        adjacency_list = self._make_adjacency_list(rvs, dist)
        statistic = self.get_graph_stat(adjacency_list)
        return statistic

    @staticmethod
    def _make_adjacency_list(rvs, dist: float) -> list[list[int]]:
        adjacency_list: list[list[int]] = []

        for i in range(len(rvs)):
            adjacency_list.append([])
            for j in range(i):
                if abs(rvs[i] - rvs[j]) < dist:
                    adjacency_list[i].append(j)
                    adjacency_list[j].append(i)

        return adjacency_list

    @staticmethod
    def _compute_dist(rvs):  # TODO (normalize for different distributions)
        return (max(rvs) - min(rvs)) / 10

    @staticmethod
    def get_graph_stat(graph: list[list[int]]):
        raise NotImplementedError("Method is not implemented")


class GraphEdgesNumberTestStatistic(AbstractGraphTestStatistic, ABC):
    @staticmethod
    @override
    def get_graph_stat(graph):
        return sum(map(len, graph)) // 2


class GraphMaxDegreeTestStatistic(AbstractGraphTestStatistic, ABC):
    @staticmethod
    @override
    def get_graph_stat(graph):
        return max(map(len, graph))
