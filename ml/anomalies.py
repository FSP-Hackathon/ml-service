import numpy as np
import stumpy

class MultivariateAnomalyDetector:
    """
    A class for detecting anomalies in a multivariate database metrics.
    """
    
    def __init__(self, time_series, window_size):
        """
        Initialize the detector with a multivariate time series and window size.
        
        :param time_series: A list of numpy arrays, where each array is a time series dimension.
        :param window_size: The size of the window to use for computing the matrix profile.
        """
        self.time_series = time_series
        self.window_size = window_size
        self.dimensions = len(time_series)
        self.matrix_profile = [np.empty(0) for _ in range(self.dimensions)]
        self.indices = [np.empty(0, dtype=int) for _ in range(self.dimensions)]

        # Compute the initial matrix profile for each dimension
        for dim in range(self.dimensions):
            self.matrix_profile[dim], self.indices[dim] = stumpy.stump(self.time_series[dim], self.window_size)
        
        # Compute the minimum matrix profile across dimensions
        self.min_matrix_profile = np.amin(np.array(self.matrix_profile), axis=0)

    def append_series(self, new_series):
        """
        Append new data to the time series and update the matrix profile.
        Each dimension is processed individually using stumpi.
        
        :param new_series: A list of new data arrays, one for each time series dimension.
        :return: True if anomalies are detected in the latest data, False otherwise.
        """
        # Check that each dimension has the same number of data points
        if not all(len(new_series[dim]) == len(new_series[0]) for dim in range(self.dimensions)):
            raise ValueError("All dimensions must have the same number of data points.")
        
        # Update the time series and the matrix profiles for each dimension
        for dim in range(self.dimensions):
            for val in new_series[dim]:
                self.time_series[dim] = np.append(self.time_series[dim], val)
                self.matrix_profile[dim], self.indices[dim] = stumpy.stumpi(
                    self.time_series[dim], self.window_size, self.matrix_profile[dim], self.indices[dim], append_val=val
                )
        
        # Recompute the minimum matrix profile across dimensions
        self.min_matrix_profile = np.amin(np.array(self.matrix_profile), axis=0)

        # Detect anomalies using the updated minimum matrix profile
        threshold = np.mean(self.min_matrix_profile) + 2 * np.std(self.min_matrix_profile)
        anomalies_in_latest_data = self.min_matrix_profile[-len(new_series[0]):] > threshold
        return np.any(anomalies_in_latest_data)

    def get_top_anomalies(self, n):
        """
        Get the top N anomalies based on the matrix profile.

        :param n: The number of top anomalies to return.
        :return: A list of indices representing the starting location of the top anomalies.
        """
        if n <= 0:
            raise ValueError("The number of anomalies must be greater than 0.")
        
        # Identify the top N anomalies
        anomaly_indices = np.argsort(-self.min_matrix_profile)[:n]
        return anomaly_indices.tolist()
