-- Run this in phpMyAdmin: Import > select file > Go
CREATE DATABASE IF NOT EXISTS fedm_system
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE fedm_system;

CREATE TABLE IF NOT EXISTS datasets (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(255)  NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  file_type     ENUM('csv','xlsx') NOT NULL,
  row_count     INT           NOT NULL DEFAULT 0,
  column_count  INT           NOT NULL DEFAULT 0,
  uploaded_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_datasets_uploaded_at (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dataset_columns (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id    INT UNSIGNED  NOT NULL,
  column_name   VARCHAR(255)  NOT NULL,
  detected_dtype VARCHAR(50)  NOT NULL,
  missing_count INT           NOT NULL DEFAULT 0,
  unique_count  INT           NOT NULL DEFAULT 0,
  column_order  INT           NOT NULL DEFAULT 0,
  CONSTRAINT fk_dc_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cleaning_actions (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id     INT UNSIGNED  NOT NULL,
  action_type    VARCHAR(50)   NOT NULL,
  target_column  VARCHAR(255)  NULL,
  parameters     JSON          NULL,
  rows_affected  INT           NOT NULL DEFAULT 0,
  sequence_order INT           NOT NULL DEFAULT 0,
  applied_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ca_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets(id) ON DELETE CASCADE ON UPDATE CASCADE,
  INDEX idx_ca_dataset_seq (dataset_id, sequence_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS insights (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id     INT UNSIGNED  NOT NULL,
  insight_type   VARCHAR(50)   NOT NULL,
  target_column  VARCHAR(255)  NULL,
  description    TEXT          NOT NULL,
  value_numeric  DECIMAL(20,4) NULL,
  generated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ins_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets(id) ON DELETE CASCADE ON UPDATE CASCADE,
  INDEX idx_ins_dataset_type (dataset_id, insight_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dashboard_charts (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id  INT UNSIGNED  NOT NULL,
  chart_type  ENUM('bar','line','pie','scatter','histogram') NOT NULL,
  x_column    VARCHAR(255)  NOT NULL,
  y_column    VARCHAR(255)  NULL,
  config      JSON          NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_dc2_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
