import pandas as pd
import logging
import os

class DataModel:
    def __init__(self):
        self.df = None
        self.original_df = None # For diff
        self.filepath = None
        self.corr_filepath = None
        self.bbox_col_index = 0 
        self.logger = logging.getLogger(__name__)
        
        # Undo Stack
        self.undo_stack = [] # List of deep copies of df
        self.max_undo = 50
        
        # Column Centers (0.0 to 1.0)
        self.column_centers = {} # col_index -> float

    def load_data(self, filepath):
        self.filepath = filepath
        base, ext = os.path.splitext(filepath)
        self.corr_filepath = f"{base}_corr{ext}"
        
        try:
            # Check if _corr exists
            if os.path.exists(self.corr_filepath):
                self.logger.info(f"Found correction file: {self.corr_filepath}")
                self.df = pd.read_csv(self.corr_filepath, sep='\t')
                # Load original for diff
                self.original_df = pd.read_csv(filepath, sep='\t')
            else:
                self.df = pd.read_csv(filepath, sep='\t')
                self.original_df = self.df.copy()
            
            self.logger.info(f"Loaded TSV with shape {self.df.shape}")
            
            # Validate first column
            if not self.df.empty:
                first_val = str(self.df.iloc[0, 0]).strip('"\' ')
                if not (first_val.startswith('[') and first_val.endswith(']')):
                    self.logger.warning(f"First column does not look like BBox data: {first_val}")
            
            # Init column centers
            config_path = filepath + ".json"
            if os.path.exists(config_path):
                try:
                    import json
                    with open(config_path, 'r') as f:
                        loaded_centers = json.load(f)
                        # Convert keys to int (json keys are strings)
                        self.column_centers = {int(k): v for k, v in loaded_centers.items()}
                    self.logger.info(f"Loaded config from {config_path}")
                except Exception as e:
                    self.logger.error(f"Failed to load config: {e}")
                    # Fallback to default
                    num_cols = len(self.df.columns)
                    for i in range(num_cols):
                        self.column_centers[i] = (i + 0.5) / num_cols
            else:
                # Default (equally spaced)
                num_cols = len(self.df.columns)
                for i in range(num_cols):
                    self.column_centers[i] = (i + 0.5) / num_cols
                
            # Push initial state
            self.push_undo()
            
        except Exception as e:
            self.logger.error(f"Failed to load TSV: {e}")
            raise

    def update_column_center(self, col_index, new_val):
        """
        Updates center for col_index and redistributes subsequent columns.
        new_val: 0.0 to 1.0
        Ignores the first column (index 0).
        """
        if col_index == 0:
            return

        self.column_centers[col_index] = new_val
        
        num_cols = len(self.df.columns)
        remaining_cols = num_cols - 1 - col_index
        
        if remaining_cols > 0:
            # Distribute remaining columns in the space (new_val, 1.0]
            # We want them equally spaced.
            # Space available: 1.0 - new_val
            # Each column gets a slot of width: space / remaining_cols? 
            # Or should we treat them as points?
            # "re-equally spaced in the remaining x axis"
            
            # Let's assume we divide the remaining space into equal chunks
            # and place centers in the middle of those chunks.
            
            space = 1.0 - new_val
            chunk = space / remaining_cols
            
            for i in range(remaining_cols):
                target_col = col_index + 1 + i
                # position = start + (i + 0.5) * chunk ? 
                # Or just linear interpolation from new_val to 1.0?
                # If we use (i+1)/(N+1) logic:
                # Let's try simple linear spacing:
                # first one at new_val + step
                # last one near 1.0
                
                # Let's use the "chunk center" logic which is robust
                center = new_val + (i + 0.5) * chunk
                self.column_centers[target_col] = center

    def push_undo(self):
        if self.df is not None:
            if len(self.undo_stack) >= self.max_undo:
                self.undo_stack.pop(0)
            self.undo_stack.append(self.df.copy())

    def undo(self):
        if len(self.undo_stack) > 1:
            self.undo_stack.pop() # Pop current state
            self.df = self.undo_stack[-1].copy() # Revert to previous
            self.auto_save()
            return True
        return False

    def save_config(self):
        if not self.filepath:
            return
        
        config_path = self.filepath + ".json"
        try:
            import json
            with open(config_path, 'w') as f:
                json.dump(self.column_centers, f)
            self.logger.info(f"Saved config to {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def auto_save(self):
        if self.corr_filepath and self.df is not None:
            try:
                self.df.to_csv(self.corr_filepath, sep='\t', index=False)
                self.logger.info(f"Auto-saved to {self.corr_filepath}")
                self.save_config() # Save config as well
            except Exception as e:
                self.logger.error(f"Auto-save failed: {e}")

    def save_data(self, filepath=None):
        # Manual save might overwrite original or just trigger auto-save
        # User request: "save after each change, keep the same name and add _corr"
        # So manual save is effectively auto-save logic, but maybe user wants to explicit save to original?
        # "save after each change" implies auto-save.
        # "keep the same name and add _corr" implies we work on _corr.
        # Let's assume manual save also updates _corr, or maybe updates original?
        # Usually manual save commits changes. Let's stick to _corr for safety as requested.
        self.auto_save()

    def is_modified(self, row, col):
        if self.original_df is None or row >= len(self.original_df):
            return True # New row is modified
        
        val_curr = self.df.iloc[row, col]
        val_orig = self.original_df.iloc[row, col]
        
        # Handle NaNs
        if pd.isna(val_curr) and pd.isna(val_orig):
            return False
            
        # String comparison
        str_curr = str(val_curr).strip() if not pd.isna(val_curr) else ""
        str_orig = str(val_orig).strip() if not pd.isna(val_orig) else ""
        
        return str_curr != str_orig

    def get_bbox(self, row_index):
        """
        Returns BBox coordinates [ymin, xmin, ymax, xmax] for a given row.
        """
        if self.df is None or row_index >= len(self.df):
            return None
        
        bbox_str = str(self.df.iloc[row_index, 0])
        try:
            # Remove brackets and split
            content = bbox_str.strip('[]"') # Also strip quotes if present
            import re
            parts = re.split(r'[;,]', content)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) != 4:
                return None
            return [int(float(p)) for p in parts]
        except ValueError:
            self.logger.error(f"Invalid BBox format at row {row_index}: {bbox_str}")
            return None

    def update_bbox(self, row_index, bbox_coords):
        """
        Updates the BBox for a row. bbox_coords = [ymin, xmin, ymax, xmax]
        """
        if self.df is None or row_index >= len(self.df):
            return
        
        self.push_undo()
        bbox_str = f"[{';'.join(map(str, bbox_coords))}]"
        self.df.iloc[row_index, 0] = bbox_str
        self.logger.debug(f"Updated row {row_index} bbox to {bbox_str}")
        self.auto_save()

    def update_cell(self, row, col, value):
        self.push_undo()
        self.df.iloc[row, col] = value
        self.auto_save()

    def revert_cell(self, row, col):
        """
        Reverts a cell to its original value from original_df.
        Returns True if successful, False otherwise.
        """
        if self.original_df is None or row >= len(self.original_df):
            self.logger.warning(f"Cannot revert cell ({row}, {col}): no original data")
            return False
        
        self.push_undo()
        original_value = self.original_df.iloc[row, col]
        self.df.iloc[row, col] = original_value
        self.logger.info(f"Reverted cell ({row}, {col}) to original value")
        self.auto_save()
        return True

    def add_row(self, bbox_coords):
        """
        Adds a new row with the given BBox. Fills other columns with empty strings.
        """
        self.push_undo()
        bbox_str = f"[{';'.join(map(str, bbox_coords))}]"
        new_row = {col: "" for col in self.df.columns}
        new_row[self.df.columns[0]] = bbox_str
        
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.logger.info(f"Added new row. Total rows: {len(self.df)}")
        self.auto_save()
        return len(self.df) - 1

    def row_count(self):
        return len(self.df) if self.df is not None else 0

    def column_count(self):
        return len(self.df.columns) if self.df is not None else 0
        
    def get_headers(self):
        return list(self.df.columns) if self.df is not None else []
