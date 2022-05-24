from abc import ABC, abstractmethod
import pandas as pd


class BaseProcessor(ABC):

    @abstractmethod
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Make transform of DataFrame"""
