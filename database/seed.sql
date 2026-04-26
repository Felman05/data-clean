USE fedm_system;

INSERT INTO datasets (name, original_filename, file_type, row_count, column_count, uploaded_at)
VALUES ('Demo Employees', 'storage/uploads/1_messy_employees.csv', 'csv', 215, 8, NOW());

INSERT INTO dataset_columns (dataset_id, column_name, detected_dtype, missing_count, unique_count, column_order)
VALUES
  (1, 'employee_id',      'int64',   0,  200, 0),
  (1, 'name',             'object',  0,  200, 1),
  (1, 'department',       'object',  5,    7, 2),
  (1, 'salary',           'float64', 8,  180, 3),
  (1, 'hire_date',        'object',  0,    9, 4),
  (1, 'status',           'object',  5,    5, 5),
  (1, 'email',            'object',  5,  200, 6),
  (1, 'years_experience', 'float64', 10, 36,  7);
