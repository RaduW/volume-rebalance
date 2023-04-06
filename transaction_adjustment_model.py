import operator
from collections import namedtuple
from copy import copy
from typing import List, Mapping, MutableMapping, Tuple, Optional

AdjustedSampleRate = namedtuple("AdjustedSampleRate", "explicit_rates, global_rate")


def adjust_sample_rate(
    classes: List[Tuple[str, float]], rate: float, total_num_classes: int, total: float
) -> Tuple[MutableMapping[str, float], float]:
    """
    Adjusts sampling rates to bring the number of samples kept in each class as close to
    the same value as possible while maintaining the overall sampling rate.

    The algorithm adjusts the explicitly given classes individually to bring them to
    the ideal sample rate and then adjusts the global sample rate for all the remaining classes.

    :param classes: a list of class id, num_samples in class
    :param rate: global rate of sampling desired
    :param total_num_classes: total number of classes (including the explicitly specified in classes)
    :param total: total number of samples in all classes (including the explicitly specified classes)

    :return: a dictionary with explicit rates for individual classes class_name->rate and
    a rate for all other (unspecified) classes.
    """

    classes = sorted(classes, key=operator.itemgetter(1))

    # total count for the explicitly specified classes
    total_explicit = get_total(classes)
    # total count for the unspecified classes
    total_implicit = total - total_explicit
    # total number of specified classes
    num_explicit_classes = len(classes)
    # total number of unspecified classes
    num_implicit_classes = total_num_classes - num_explicit_classes

    total_budget = total * rate
    budget_per_class = total_budget / total_num_classes

    implicit_budget = budget_per_class * num_implicit_classes
    explicit_budget = budget_per_class * num_explicit_classes

    if num_explicit_classes == total_num_classes:
        # we have specified all classes
        explicit_rates = adjust_sample_rate_full(classes, rate)
        implicit_rate = rate  # doesn't really matter since everything is explicit
    elif total_implicit < implicit_budget:
        # we would not be able to spend all implicit budget we can only spend
        # a maximum of total_implicit, set the implicit rate to 1
        # and reevaluate the available budget for the explicit classes
        implicit_rate = 1
        # we spent all we could on the implicit classes see what budget we
        # have left
        explicit_budget = total_budget - total_implicit
        # calculate the new global rate for the explicit transactions that
        # would bring the overall rate to the desired rate
        explicit_rate = explicit_budget / total_explicit
        explicit_rates = adjust_sample_rate_full(classes, explicit_rate)
    elif total_explicit < explicit_budget:
        # we would not be able to spend all explicit budget we can only
        # send a maximum of total_explicit so set the explicit rate to 1 for
        # all explicit classes and reevaluate the available budget for the implicit classes
        explicit_rates = {name: 1.0 for name, _count in classes}

        # calculate the new global rate for the implicit transactions
        implicit_budget = total_budget - total_explicit
        implicit_rate = implicit_budget / total_implicit
    else:
        # we can spend all the implicit budget on the implicit classes
        # and all the explicit budget on the explicit classes
        # the calculation of rates can be done independently for explicit and
        # implicit classes
        implicit_rate = implicit_budget / total_implicit
        explicit_rate = explicit_budget / total_explicit
        explicit_rates = adjust_sample_rate_full(classes, explicit_rate)
    return explicit_rates, implicit_rate


def adjust_sample_rate_full(
    transactions: List[Tuple[str, float]], rate: float
) -> MutableMapping[str, float]:
    """
    Resample all classes to their ideal size.

    Ideal size is defined as the minimum of:
    - num_samples_in_class ( i.e. no sampling, rate 1.0)
    - total_num_samples * rate / num_classes

    """
    transactions = copy(transactions)
    ret_val = {}
    num_transactions = get_total(transactions)
    # calculate how many transactions we are allowed to keep overall
    # this will allow us to pass transactions between different transaction types
    total_budget = num_transactions * rate
    while transactions:
        num_types = len(transactions)
        # We recalculate the budget per type every iteration to
        # account for the cases where, in the previous step we couldn't
        # spend all the allocated budget for that type.
        budget_per_transaction_type = total_budget / num_types
        name, count = transactions.pop(0)
        if count < budget_per_transaction_type:
            # we have fewer transactions in this type than the
            # budget, all we can do is to keep everything
            ret_val[name] = 1.0  # not enough samples, use all
            total_budget -= count
        else:
            # we have enough transactions in current the class
            # we want to only keep budget_per_transactions
            transaction_rate = budget_per_transaction_type / count
            ret_val[name] = transaction_rate
            total_budget -= budget_per_transaction_type
    return ret_val


def adjust_sample_rate_v2(
    classes: List[Tuple[str, float]], rate: float, total_num_classes: int, total: float, intensity: float,
) -> Tuple[MutableMapping[str, float], float]:
    """
    Adjusts sampling rates to bring the number of samples kept in each class as close to
    the same value as possible while maintaining the overall sampling rate.

    The algorithm adjusts the explicitly given classes individually to bring them to
    the ideal sample rate and then adjusts the global sample rate for all the remaining classes.

    :param classes: a list of class id, num_samples in class
    :param rate: global rate of sampling desired
    :param total_num_classes: total number of classes (including the explicitly specified in classes)
    :param intensity: the adjustment strength 0: no adjustment, 1: try to bring everything to mean
    :param total: total number of samples in all classes (including the explicitly specified classes)

    :return: a dictionary with explicit rates for individual classes class_name->rate and
    a rate for all other (unspecified) classes.
    """

    classes = sorted(classes, key=operator.itemgetter(1))

    # total count for the explicitly specified classes
    total_explicit = get_total(classes)
    # total count for the unspecified classes
    total_implicit = total - total_explicit
    # total number of specified classes
    num_explicit_classes = len(classes)
    # total number of unspecified classes
    num_implicit_classes = total_num_classes - num_explicit_classes

    total_budget = total * rate
    budget_per_class = total_budget / total_num_classes

    implicit_budget = budget_per_class * num_implicit_classes
    explicit_budget = budget_per_class * num_explicit_classes

    if num_explicit_classes == total_num_classes:
        # we have specified all classes
        explicit_rates, _used = adjust_sample_rate_full_v2(classes, rate=rate, intensity=intensity, min_budget=None)
        implicit_rate = rate  # doesn't really matter since everything is explicit
    elif total_implicit < implicit_budget:
        # we would not be able to spend all implicit budget we can only spend
        # a maximum of total_implicit, set the implicit rate to 1
        # and reevaluate the available budget for the explicit classes
        implicit_rate = 1
        # we spent all we could on the implicit classes see what budget we
        # have left
        explicit_budget = total_budget - total_implicit
        # calculate the new global rate for the explicit transactions that
        # would bring the overall rate to the desired rate
        explicit_rate = explicit_budget / total_explicit
        explicit_rates, _used = adjust_sample_rate_full_v2(classes, explicit_rate, intensity=intensity, min_budget=None)
    elif total_explicit < explicit_budget:
        # we would not be able to spend all explicit budget we can only
        # send a maximum of total_explicit so set the explicit rate to 1 for
        # all explicit classes and reevaluate the available budget for the implicit classes
        explicit_rates = {name: 1.0 for name, _count in classes}

        # calculate the new global rate for the implicit transactions
        implicit_budget = total_budget - total_explicit
        implicit_rate = implicit_budget / total_implicit
    else:
        # we can spend all the implicit budget on the implicit classes
        # and all the explicit budget on the explicit classes
        # see exactly how much we spend on the explicit classes
        # and leave the rest for the implicit classes

        # calculate what is the minimum amount we need to spend on the
        # explicit classes (so that we maintain the overall rate)
        # if it is <= 0 then we don't have a minimum
        minimum_explicit_budget = total_budget - total_implicit
        explicit_rate = explicit_budget / total_explicit

        explicit_rates, used = adjust_sample_rate_full_v2(
            classes=classes,
            rate=explicit_rate,
            intensity=intensity,
            min_budget=minimum_explicit_budget
        )
        implicit_rate = implicit_budget / total_implicit
    return explicit_rates, implicit_rate


def adjust_sample_rate_full_v2(items: List[Tuple[str, float]], rate: float, intensity: float,
                               min_budget: Optional[float] = None) -> Tuple[MutableMapping[str, float], float]:
    """
    Tries to calculate rates that brings all counts close to the ideal count

    The intensity controls how close, 0 intensity leaves the items unchanged, 1 brings the items to the
    ideal count ( or rate=1.0 if ideal count is too high).

    :param items: The items to be balanced
    :param rate: The overall rate necessary
    :param intensity: How close to the ideal should we go from our current position (0=do not change, 1 go to ideal)
    :param min_budget: Ensure that we use at least min_budget (in order to keep the overall rate)

    :return: A mapping with the frequency for all items + the amount of items used ( it should allways be at least
    minimum_consumption if passed)
    """

    classes = sorted(items, key=operator.itemgetter(1))
    total = get_total(classes)
    num_classes = len(classes)

    if min_budget is None:
        # use exactly what we need (default handling when we resize everything)
        min_budget = total * rate

    assert total >= min_budget
    ideal = total * rate / num_classes

    used_budget = 0

    ret_val = {}
    while classes:
        name, count = classes.pop()
        if ideal * num_classes < min_budget:
            # if we keep to our ideal we will not be able to use the minimum budget (readjust our target)
            ideal = min_budget / num_classes
        # see what's the difference from our ideal
        sampled = count * rate
        delta = ideal - sampled
        correction = delta * intensity
        desired_count = sampled + correction

        if desired_count > count:
            # we need more than we have, the best we can do is give all, i.e. rate = 1.0
            ret_val[name] = 1.0
            used = count
        else:
            # we can spend what we want
            ret_val[name] = desired_count / count
            used = desired_count
        min_budget -= used
        used_budget += used
        num_classes -= 1

    return ret_val, used_budget


def adjust_sample_rate_full_x(
    transactions: List[Tuple[str, float]], rate: float, intensity: float = 1.0
) -> MutableMapping[str, float]:
    """
    Resample all classes to their ideal size.

    Ideal size is defined as the minimum of:
    - num_samples_in_class ( i.e. no sampling, rate 1.0)
    - total_num_samples * rate / num_classes

    """
    transactions = copy(transactions)
    ret_val = {}
    num_transactions = get_total(transactions)
    # calculate how many transactions we are allowed to keep overall
    # this will allow us to pass transactions between different transaction types
    total_budget = num_transactions * rate
    while transactions:
        num_types = len(transactions)
        # We recalculate the budget per type every iteration to
        # account for the cases where, in the previous step we couldn't
        # spend all the allocated budget for that type.
        budget_per_transaction_type = total_budget / num_types
        name, count = transactions.pop(0)
        # calculate the correction as a factor of the distance between what we have and what is ideal
        correction = (budget_per_transaction_type - count * rate) * intensity
        # calculate where we want to be:
        desired_sample_size = count * rate + correction
        if count < desired_sample_size:
            # we have fewer transactions in this type than the
            # budget, all we can do is to keep everything
            ret_val[name] = 1.0  # not enough samples, use all
            total_budget -= count
        else:
            # we have enough transactions in current the class
            # we want to only keep budget_per_transactions
            transaction_rate = desired_sample_size / count
            ret_val[name] = transaction_rate
            total_budget -= desired_sample_size
    return ret_val


def get_total(transactions: List[Tuple[str, float]]) -> float:
    ret_val = 0
    for _, v in transactions:
        ret_val += v
    return ret_val


def get_num_sampled_elements(
    transactions: List[Tuple[str, int]], trans_dict: Mapping[str, float], global_rate: float
) -> float:
    num_transactions = 0.0
    for name, count in transactions:
        transaction_rate = trans_dict.get(name)
        if transaction_rate:
            num_transactions += transaction_rate * count
        else:
            num_transactions += global_rate * count
    return num_transactions
