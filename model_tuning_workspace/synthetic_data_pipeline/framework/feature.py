import random
from abc import abstractmethod
from enum import Enum
from typing import List, Optional, Union, Tuple, Dict

class TopLevelFeature:

    def __init__(
            self,
            name: str,
    ):
        self.name = name

    @abstractmethod
    def init_sub_feature_values(self) -> None:
        raise NotImplementedError("Subclasses should implement this method")

    @abstractmethod
    def build_prompt(self) -> str:
        raise NotImplementedError("Subclasses should implement this method")

    @abstractmethod
    def validate_sub_features(self, output: str) -> bool:
        raise NotImplementedError("Subclasses should implement this method")

    @abstractmethod
    def serialize(self) -> dict:
        raise NotImplementedError("Subclasses should implement this method")

class FeatureType(Enum):
    CORE = "core"
    DIVERSITY = "diversity"

class Feature:
    def __init__(
            self,
            name: str,
            feature_type: FeatureType,
            options: Union[
                List[str], # ["option1", "option2", ...]
                List[Tuple[str, float]], # [("option1", weight1), ("option2", weight2), ...]
                Dict[str, float] # {"option1": weight1, "option2": weight2, ...}
            ] = list
    ):
        self.name = name
        self.feature_type = feature_type
        self.selected_value: Optional[str] = None

        # Convert options to standardized format of (value, weight) tuples
        if isinstance(options, dict):
            self.options = [(value, weight) for value, weight in options.items()]
        elif isinstance(options, list):
            if all(isinstance(opt, str) for opt in options):
                # If all options are strings, assign equal weights
                self.options = [(opt, 1.0) for opt in options]
            elif all(isinstance(opt, tuple) and len(opt) == 2 for opt in options):
                self.options = options
            else:
                raise ValueError("Options must be either all strings or all (value, weight) tuples")

    def select_value(self) -> str:
        values, weights = zip(*self.options)
        self.selected_value = random.choices(values, weights=weights, k=1)[0]
        return self.selected_value

    def serialize(self) -> tuple[str, str]:
        """Returns a tuple of (feature_name, selected_value) for easy dict unpacking"""
        return self.name, self.selected_value
