# COVID-19 Project

This project analyzes COVID-19 data using SQL to uncover insights about cases, deaths, and vaccinations globally and by country.  
The analysis is performed on two main datasets: `CovidDeaths` and `CovidVaccinations` from the database `COVID19PortfolioProject`.

## Key Steps & Analysis

### 1. Data Exploration
- Selected relevant columns for analysis.
- Filtered out aggregated locations (like continents and world) to focus on country-level data.

### 2. Cases vs. Deaths
- Calculated the likelihood of dying from COVID-19 for each location and date:  
  `death_percentage = (total_deaths / total_cases) * 100`
- Investigated these metrics specifically for Canada.

### 3. Infection Rate vs. Population
- Computed what percentage of a country's population has been infected:
  - `percent_population_infected = (total_cases / population) * 100`
- Identified countries with the highest infection rates.

### 4. Death Rate Analysis
- Found countries with the highest death counts per population.
- Analyzed continents with the highest death counts.

### 5. Global Trends
- Aggregated global numbers for cases and deaths by date.
- Calculated global death percentage per day.

### 6. Vaccination Analysis
- Merged death and vaccination datasets to analyze vaccination progress by country and continent.
- Used window functions to calculate rolling totals of people vaccinated.

### 7. Advanced SQL Techniques
- Utilized Common Table Expressions (CTEs) to structure analysis of population vs. vaccination.
- Created temporary tables to store and analyze percent of population vaccinated.
- Built SQL views for later visualizations and reporting.

## Example SQL Features Used

- **Aggregate Functions:** `MAX`, `SUM`
- **Window Functions:**  
  `SUM(...) OVER (Partition by ... Order by ...)`
- **Joins:**  
  Joining deaths and vaccinations by location and date.
- **Grouping & Filtering:**  
  `GROUP BY`, `WHERE`, and filtering for continents/countries.
- **CTEs:**  
  For readable, reusable queries.
- **Temp Tables & Views:**  
  For storing intermediate and final results.

## How to Use

1. Ensure your SQL environment has access to the `COVID19PortfolioProject` database with tables `CovidDeaths` and `CovidVaccinations`.
2. Run the queries step by step to explore different aspects of the data.
3. Use the final views and temp tables for dashboarding or further visualization in tools like Tableau, PowerBI, or Python.

## Insights Uncovered

- Country-level infection and death rates.
- Temporal trends in global cases and deaths.
- Vaccination progress and its relation to population.
- Identification of countries and continents most affected.
