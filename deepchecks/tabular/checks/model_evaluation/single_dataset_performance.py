# ----------------------------------------------------------------------------
# Copyright (C) 2021-2022 Deepchecks (https://www.deepchecks.com)
#
# This file is part of Deepchecks.
# Deepchecks is distributed under the terms of the GNU Affero General
# Public License (version 3 or later).
# You should have received a copy of the GNU Affero General Public License
# along with Deepchecks.  If not, see <http://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------
#
"""Module containing the single dataset performance check."""
from numbers import Number
from typing import TYPE_CHECKING, Callable, Dict, List, TypeVar, Union, cast

import pandas as pd

from deepchecks.core import CheckResult, ConditionCategory, ConditionResult
from deepchecks.core.errors import DeepchecksValueError
from deepchecks.core.reduce_classes import ReduceMetricClassMixin
from deepchecks.tabular import Context
from deepchecks.tabular.base_checks import SingleDatasetCheck
from deepchecks.utils.docref import doclink
from deepchecks.utils.strings import format_number

if TYPE_CHECKING:
    from deepchecks.core.checks import CheckConfig

__all__ = ['SingleDatasetPerformance']


SDP = TypeVar('SDP', bound='SingleDatasetPerformance')


class SingleDatasetPerformance(SingleDatasetCheck, ReduceMetricClassMixin):
    """Summarize given model performance on the train and test datasets based on selected scorers.

    Parameters
    ----------
    scorers : Union[List[str], Dict[str, Union[str, Callable]]], default: None
        List of scorers to use. If None, use default scorers.
        Scorers can be supplied as a list of scorer names or as a dictionary of names and functions.
    """

    def __init__(self,
                 scorers: Union[List[str], Dict[str, Union[str, Callable]]] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.scorers = scorers

    def run_logic(self, context: Context, dataset_kind) -> CheckResult:
        """Run check."""
        dataset = context.get_data_by_kind(dataset_kind)
        model = context.model
        scorers = context.get_scorers(self.scorers, use_avg_defaults=True)

        results = []
        classes = dataset.classes
        label = cast(pd.Series, dataset.label_col)
        if context.with_display:
            n_samples = label.groupby(label).count()
        else:
            n_samples = dict(zip(classes, [None] * len(classes)))
        for scorer in scorers:
            scorer_value = scorer(model, dataset)
            if isinstance(scorer_value, Number):
                results.append([pd.NA, scorer.name, scorer_value, len(label)])
            else:
                results.extend(
                    [[class_name, scorer.name, class_score, n_samples[class_name]]
                     for class_score, class_name in zip(scorer_value, classes)])
        results_df = pd.DataFrame(results, columns=['Class', 'Metric', 'Value', 'Number of samples'])

        if context.with_display:
            display = [results_df]
        else:
            display = []

        return CheckResult(results_df, header='Single Dataset Performance', display=display)

    def config(
        self,
        include_version: bool = True
    ) -> 'CheckConfig':
        """Return check configuration."""
        if isinstance(self.scorers, dict):
            for k, v in self.scorers.items():
                if not isinstance(v, str):
                    reference = doclink(
                        'tabular-builtin-metrics',
                        template='For a list of built-in scorers please refer to {link}'
                    )
                    raise ValueError(
                        'Only built-in scorers are allowed when serializing check instances. '
                        f'{reference}. Scorer name: {k}'
                    )
        return super().config(include_version=include_version)

    def reduce_output(self, check_result: CheckResult) -> Dict[str, float]:
        """Return the values of the metrics for the dataset provided in a {metric: value} format."""
        result = {(row['Metric'], str(row['Class'])): row['Value'] for _, row in check_result.value.iterrows()}
        for key in [key for key in result.keys() if key[1] == '<NA>']:
            result[key[0]] = result.pop(key)
        return result

    def add_condition_greater_than(self, threshold: float, metrics: List[str] = None, class_mode: str = 'all') -> SDP:
        """Add condition - the selected metrics scores are greater than the threshold.

        Parameters
        ----------
        threshold: float
            The threshold that the metrics result should be grater than.
        metrics: List[str]
            The names of the metrics from the check to apply the condition to. If None, runs on all the metrics that
            were calculated in the check.
        class_mode: str, default: 'all'
            The decision rule over the classes, one of 'any', 'all', class name. If 'any', passes if at least one class
            result is above the threshold, if 'all' passes if all the class results are above the threshold,
            class name, passes if the result for this specified class is above the threshold.
        """

        def condition(check_result, metrics_to_check=metrics):
            metrics_to_check = check_result['Metric'].unique() if metrics_to_check is None else metrics_to_check
            metrics_pass = []

            for metric in metrics_to_check:
                if metric not in check_result.Metric.unique():
                    raise DeepchecksValueError(f'The requested metric was not calculated, the metrics calculated in '
                                               f'this check are: {check_result.Metric.unique()}.')
                metric_result = check_result[check_result['Metric'] == metric]
                if class_mode == 'all':
                    metrics_pass.append(min(metric_result['Value']) > threshold)
                elif class_mode == 'any':
                    metrics_pass.append(max(metric_result['Value']) > threshold)
                elif str(class_mode) in [str(x) for x in metric_result['Class'].unique()]:
                    metrics_pass.append(metric_result['Value'][class_mode] > threshold)
                else:
                    raise DeepchecksValueError(f'class_mode expected be one of the classes in the check results or any '
                                               f'or all, received {class_mode}.')

            if all(metrics_pass):
                return ConditionResult(ConditionCategory.PASS, 'Passed for all of the metrics.')
            else:
                failed_metrics = ([a for a, b in zip(metrics_to_check, metrics_pass) if not b])
                return ConditionResult(ConditionCategory.FAIL, f'Failed for metrics: {failed_metrics}')

        return self.add_condition(f'Selected metrics scores are greater than {format_number(threshold)}', condition)
