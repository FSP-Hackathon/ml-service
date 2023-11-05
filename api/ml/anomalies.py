import numpy as np
import stumpy

class MultidimensionalMatrixProfile:
    """
    A class to find anomalies of PostgreSQL metrics time series without overlapping.
    
    Attributes:
    time_series (np.ndarray): The multidimensional time series data.
    window_size (int): The window size for the matrix profile computation.
    matrix_profile (np.ndarray): The computed matrix profile.
    profile_indices (np.ndarray): The profile indices (motif indices) for the matrix profile.
    """

    def __init__(self, time_series, window_size):
        """
        Initialize the class with a multidimensional time series and window size.
        Immediately computes the matrix profile.
        
        Parameters:
        time_series (np.ndarray): A multidimensional array where each column represents a dimension of the time series.
        window_size (int): The window size for the matrix profile computation.
        """
        self.time_series = time_series
        self.window_size = window_size
        self.matrix_profile, self.profile_indices = stumpy.mstump(self.time_series, self.window_size, discords=True)

    def update(self, new_data):
        """
        Update the time series with new data and recompute the matrix profile.
        
        Parameters:
        new_data (np.ndarray): New data to be added to the time series. Should have the same number of dimensions.
        
        Returns:
        bool: True if the latest points are anomalies, otherwise False.
        """
        self.time_series = np.hstack((self.time_series, new_data.reshape(-1, 1)))
        updated_matrix_profile, updated_profile_indices = stumpy.mstump(self.time_series, self.window_size)
        
        # Extract the matrix profile values for the last window
        last_profile_values = updated_matrix_profile[-1, :]
        
        # Calculate the mean and standard deviation for comparison
        mean_profile_value = np.mean(last_profile_values)
        std_profile_value = np.std(last_profile_values)

        # Check if any of the last window's matrix profile values are considered anomalies
        # We use the .any() function to see if any value fulfills the anomaly condition
        is_anomaly = (last_profile_values > mean_profile_value + 2 * std_profile_value).any()
    
        if is_anomaly:
            return True
        else:
            return False

    def get_top_anomalies(self, n):
        """
        Get the top n anomalies from the matrix profile without overlaps.
        
        Parameters:
        n (int): Number of top anomalies to retrieve.
        
        Returns:
        list of tuples: Each tuple contains the starting index of the anomaly and its corresponding matrix profile value.
        """
        # Sort the matrix profile values in descending order to find the highest peaks (anomalies)
        ordered_indices = np.argsort(-self.matrix_profile[:, 0])
        anomalies = []
        for idx in ordered_indices:
            if len(anomalies) >= n:
                break
            # Ensure that there is no overlap with already identified anomalies
            if not any([(idx >= anomaly[0] and idx < anomaly[0] + self.window_size) for anomaly in anomalies]):
                anomalies.append((idx, self.matrix_profile[idx, 0]))
        return anomalies
    
    def check_last_10mins(self):
        if len(self.matrix_profile[0]) < 120:
            return False
    
        last_profile_values = self.matrix_profile[:, -1]
        print(last_profile_values.shape)
        # Calculate the mean and standard deviation for comparison
        mean_profile_value = np.mean(self.matrix_profile[:, -40:], axis=1)
        std_profile_value = np.std(self.matrix_profile[:, -40:], axis=1)
        print(last_profile_values, mean_profile_value, std_profile_value)
        # Check if any of the last window's matrix profile values are considered anomalies
        # We use the .any() function to see if any value fulfills the anomaly condition
        is_anomaly = (last_profile_values > mean_profile_value + 2 * std_profile_value).any()
    
        if is_anomaly:
            return True
        else:
            return False