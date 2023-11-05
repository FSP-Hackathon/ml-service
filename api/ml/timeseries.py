import pandas as pd
from etna.datasets.tsdataset import TSDataset
from etna.models import CatBoostMultiSegmentModel
from etna.transforms import DateFlagsTransform


class MultivariateTimeSeriesPredictor:
    def __init__(self, timestamps, values):
        """
        Initialize the class with timestamps and values of the multivariate time series.

        :param timestamps: NumPy array of timestamps.
        :param values: NumPy array of the multivariate time series values.
        """
        if not isinstance(timestamps, np.ndarray) or not isinstance(values, np.ndarray):
            raise ValueError("Both timestamps and values must be numpy arrays.")
        if len(timestamps.shape) != 1:
            raise ValueError("Timestamps array must be one-dimensional.")
        if len(values.shape) != 2:
            raise ValueError("Values array must be two-dimensional.")

        self.timestamps = timestamps
        self.values = values
        self.model = CatBoostMultiSegmentModel()
        self.ts_dataset = self._create_ts_dataset()

    def _create_ts_dataset(self):
        """
        Create TSDataset from the provided timestamps and values.

        :return: TSDataset.
        """
        df = pd.DataFrame(self.values, index=self.timestamps)
        df = df.reset_index().melt(id_vars=['index'], var_name='segment', value_name='target')
        df.rename(columns={'index': 'timestamp'}, inplace=True)

        df['segment'] = df['segment'].apply(lambda x: f'segment_{x}')

        return TSDataset(df=df)

    def fit(self):
        """
        Train the model on the time series data.
        """
        self.ts_dataset.fit_transform([DateFlagsTransform()])
        self.model.fit(self.ts_dataset)

    def predict(self, steps):
        """
        Predict the time series values for a given number of steps forward.

        :param steps: Number of time steps to predict.
        :return: DataFrame with predictions for each segment.
        """
        future = self.ts_dataset.make_future(steps)
        forecast = self.model.forecast(future)
        return forecast.to_pandas().reset_index()
