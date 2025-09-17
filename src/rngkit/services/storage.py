import csv
import os
from contextlib import ExitStack
from datetime import datetime
from typing import Iterable, List

import pandas as pd
import numpy as np
import xlsxwriter  # type: ignore
from bitstring import BitArray  # type: ignore


def write_csv_count(count: int, filename_stem: str) -> None:
    """Write a count entry to a CSV file.
    
    Args:
        count: Number of '1' bits counted
        filename_stem: Base filename without extension
    """
    now = datetime.now().strftime("%Y%m%dT%H%M%S")
    path = f"{filename_stem}.csv"
    try:
        with open(path, 'a', newline='') as f:
            csv.writer(f).writerow([now, count])
    except (OSError, IOError) as e:
        raise RuntimeError(f"Failed to write CSV count: {e}")


def read_bin_counts(file_path: str, block_bits: int) -> pd.DataFrame:
    """Read binary file and count '1' bits per block.
    
    Args:
        file_path: Path to binary file
        block_bits: Number of bits per block (must be divisible by 8)
        
    Returns:
        DataFrame with columns ['samples', 'ones']
        
    Raises:
        ValueError: If block_bits is not divisible by 8
        RuntimeError: If file cannot be read
    """
    if block_bits <= 0 or (block_bits % 8) != 0:
        raise ValueError("block_bits must be positive and divisible by 8")
    
    data_list: List[List[int]] = []
    try:
        with open(file_path, 'rb') as binary_file:
            block = 1
            while True:
                data = binary_file.read(block_bits // 8)
                if not data:
                    break
                ones = BitArray(data).count(1)
                data_list.append([block, ones])
                block += 1
    except (OSError, IOError) as e:
        raise RuntimeError(f"Failed to read binary file: {e}")
    
    return pd.DataFrame(data_list, columns=['samples', 'ones'])


def read_csv_counts(file_path: str) -> pd.DataFrame:
    """Read CSV file with time and count data.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        DataFrame with columns ['time', 'ones'] where time is formatted as HH:MM:SS
        
    Raises:
        RuntimeError: If file cannot be read
    """
    try:
        df = pd.read_csv(file_path, header=None, names=['time', 'ones'])
        df['time'] = pd.to_datetime(df['time']).apply(lambda x: x.strftime('%H%M%S'))
        return df
    except (OSError, IOError, pd.errors.EmptyDataError) as e:
        raise RuntimeError(f"Failed to read CSV file: {e}")


def add_zscore(df: pd.DataFrame, block_bits: int) -> pd.DataFrame:
    """Add Z-score calculation to DataFrame.
    
    Args:
        df: DataFrame with 'ones' column
        block_bits: Number of bits per block for statistical calculation
        
    Returns:
        DataFrame with added 'cumulative_mean' and 'z_test' columns
        
    Raises:
        ValueError: If block_bits is not positive
    """
    if block_bits <= 0:
        raise ValueError("block_bits must be positive")
    
    expected_mean = 0.5 * block_bits
    expected_std_dev = np.sqrt(block_bits * 0.5 * 0.5)
    df['cumulative_mean'] = df['ones'].expanding().mean()
    df['z_test'] = (df['cumulative_mean'] - expected_mean) / (expected_std_dev / np.sqrt(df.index + 1))
    return df


def write_excel_with_chart(df: pd.DataFrame, file_path: str, block_bits: int, interval: int) -> str:
    """Write DataFrame to Excel file with Z-score chart.
    
    Args:
        df: DataFrame with Z-score data
        file_path: Input file path (used to generate output path)
        block_bits: Number of bits per block
        interval: Sample interval in seconds
        
    Returns:
        Path to created Excel file
        
    Raises:
        ValueError: If parameters are invalid
        RuntimeError: If Excel file cannot be created
    """
    if block_bits <= 0 or interval <= 0:
        raise ValueError("block_bits and interval must be positive")
    
    out_path = os.path.splitext(file_path)[0] + '.xlsx'
    try:
        writer = pd.ExcelWriter(out_path, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Zscore', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Zscore']
        chart = workbook.add_chart({'type': 'line'})
        chart.add_series({'categories': ['Zscore', 1, 0, len(df), 0], 'values': ['Zscore', 1, 3, len(df), 3]})
        chart.set_title({'name': os.path.basename(file_path)})
        chart.set_x_axis({'name': f'Number of Samples - one sample every {interval} second(s)', 'date_axis': True})
        chart.set_y_axis({'name': f'Z-Score - Sample Size = {block_bits} bits'})
        chart.set_legend({'none': True})
        worksheet.insert_chart('F2', chart)
        writer.close()
        return out_path
    except Exception as e:
        raise RuntimeError(f"Failed to create Excel file: {e}")


def concat_csv_files(all_filenames: Iterable[str], out_stem: str) -> str:
    """Concatenate multiple CSV files into one.
    
    Args:
        all_filenames: Iterable of CSV file paths to concatenate
        out_stem: Base name for output file (without extension)
        
    Returns:
        Path to concatenated CSV file
        
    Raises:
        ValueError: If no filenames provided
        RuntimeError: If files cannot be read or written
    """
    filenames_list = list(all_filenames)
    if not filenames_list:
        raise ValueError("No filenames provided")
    
    out_path = os.path.join(os.path.dirname(filenames_list[0]), f"{out_stem}.csv")
    try:
        with ExitStack() as stack:
            files = [stack.enter_context(open(fname)) for fname in filenames_list]
            with open(out_path, 'a') as out:
                for f in files:
                    for line in f:
                        out.write(line)
        return out_path
    except (OSError, IOError) as e:
        raise RuntimeError(f"Failed to concatenate CSV files: {e}")


