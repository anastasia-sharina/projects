# Nashville Housing Project

This SQL project focuses on cleaning and transforming the Nashville Housing dataset to prepare it for analysis and visualization.  
Key data wrangling steps are performed using SQL queries to ensure consistency, improve data quality, and enable deeper insights.

## Key Steps & Transformations

### 1. Date Standardization
- Converted the `SaleDate` field to a standard `DATE` format.
- Added a new column `SaleDateConverted` to store the standardized date.
- Dropped unnecessary temporary columns created during transformation.

### 2. Populating Missing Property Addresses
- Used self-joins to fill in missing `PropertyAddress` values by matching records with the same `ParcelID`.
- Applied updates so that missing addresses are replaced with existing values from matching parcels.

### 3. Splitting Address Fields
- Separated `PropertyAddress` into two new columns:  
  - `PropertySplitAddress` (street address)
  - `PropertySplitCity` (city)
- Used string manipulation functions (`SUBSTRING`, `CHARINDEX`) for splitting.

### 4. Splitting Owner Address into Address, City, State
- Used `PARSENAME` and `REPLACE` functions to break out `OwnerAddress` into three new columns:
  - `OwnerSplitAddress`
  - `OwnerSplitCity`
  - `OwnerSplitState`

### 5. Standardizing "Sold As Vacant" Field
- Converted values in the `SoldAsVacant` field from 'Y'/'N' to 'Yes'/'No' for clarity and consistency.

### 6. Removing Duplicates
- Identified duplicates using `ROW_NUMBER()` window function, partitioned by key fields.
- Provided a way to filter and remove duplicate records, keeping only the first occurrence.

## SQL Techniques Used

- **Self-joins** for data imputation.
- **String manipulation**: `SUBSTRING`, `CHARINDEX`, `PARSENAME`, `REPLACE`.
- **Date conversion**: `CONVERT(Date, ...)`.
- **CASE statements** for data standardization.
- **Window functions**: `ROW_NUMBER()` for duplicate detection.
- **ALTER TABLE** for schema updates (adding/dropping columns).

## Usage

- Run the queries step by step in your SQL environment connected to the `PortfolioProject` database.
- After cleaning, use the transformed `NashvilleHousing` table for further analysis, reporting, or visualization.

## Insights Enabled

- Consistent date formats for time-based analysis.
- Complete property and owner address fields for location-based insights.
- Standardized categorical variables.
- Deduplicated dataset for accurate results.

---

**This workflow demonstrates essential SQL data cleaning techniques for real-world housing datasets. Feel free to adapt or extend the queries for your own projects!**