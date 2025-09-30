Select *
From COVID19PortfolioProject..CovidDeaths
Where continent is not null
Order by 3,4

-- Select *
-- From COVID19PortfolioProject..CovidVaccinations
-- Order by 3,4

-- Selecting data for analysis

Select Location, date, total_cases, new_cases, total_deaths, population
From COVID19PortfolioProject..CovidDeaths
Where continent is not null
Order by 1,2


-- Looking at Total Cases vs Total Deaths
-- Shows likelihood of dying of Covid

Select Location, date, total_cases, total_deaths, (total_deaths/total_cases)*100 AS death_percentage
From COVID19PortfolioProject..CovidDeaths
Where continent is not null
Order by 1,2


-- Looking at Total Cases vs Total Deaths in Canada
-- Shows likelihood of dying of Covid in Canada

Select Location, date, total_cases, total_deaths, (total_deaths/total_cases)*100 AS death_percentage
From COVID19PortfolioProject..CovidDeaths
Where location like '%Canada%'
Where continent is not null
Order by 1,2


-- Looking at Total Cases vs Population
-- Shows what percentage of population got Covid

Select Location, date, total_cases, population, (total_cases/population)*100 AS percent_population_infected
From COVID19PortfolioProject..CovidDeaths
-- Where location like '%Canada%'
Where continent is not null
Order by 1,2


-- Looking at Countries with Highest Infection Rate compared to Population

Select Location, population, MAX(total_cases) AS highest_infection_count, MAX((total_cases/population))*100 AS percent_population_infected
From COVID19PortfolioProject..CovidDeaths
-- Where location like '%Canada%'
Where continent is not null
Group by Location, population
Order by percent_population_infected desc


-- Showing Countries with Highest Death Count per Population

Select Location, MAX(cast(total_deaths AS int)) AS total_death_count
From COVID19PortfolioProject..CovidDeaths
-- Where location like '%Canada%'
Where continent is not null
Group by Location
Order by total_death_count desc


-- Breaking things down by continents
-- Showing the continents with the highest death count per population

Select location, MAX(cast(total_deaths AS int)) AS total_death_count
From COVID19PortfolioProject..CovidDeaths
-- Where location like '%Canada%'
Where continent is null
Group by location
Order by total_death_count desc


-- Global numbers

Select date, SUM(new_cases) AS total_cases, SUM(cast(new_deaths as int)) AS total_deaths, SUM(cast(new_deaths as int))/SUM(new_cases)*100 AS death_percentage
From COVID19PortfolioProject..CovidDeaths
-- Where location like '%Canada%'
Where continent is not null
Group by date
Order by 1,2


-- Looking at Total Population vs Vaccinations

Select dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations
, SUM(CONVERT(int,vac.new_vaccinations)) OVER (Partition by dea.location Order by dea.location, dea.date) AS rolling_people_vaccinated
--, (rolling_people_vaccinated/population)*100
From COVID19PortfolioProject..CovidDeaths dea
Join COVID19PortfolioProject..CovidVaccinations vac
	On dea.location = vac.location
	and dea.date = vac.date
Where dea.continent is not null
Order by 2,3


-- Use CTE

With PopvsVac (continent, location, date, population, new_vaccinations, rolling_people_vaccinated)
as 
(
Select dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations
, SUM(CONVERT(int,vac.new_vaccinations)) OVER (Partition by dea.location Order by dea.location, dea.date) AS rolling_people_vaccinated
--, (rolling_people_vaccinated/population)*100
From COVID19PortfolioProject..CovidDeaths dea
Join COVID19PortfolioProject..CovidVaccinations vac
	On dea.location = vac.location
	and dea.date = vac.date
Where dea.continent is not null
-- Order by 2,3
)
Select *, (rolling_people_vaccinated/population)*100
From PopvsVac


-- Temp Table

DROP Table if exists #percent_population_vaccinated
Create Table #percent_population_vaccinated
(
continent nvarchar(255),
location nvarchar(255),
date datetime,
population numeric,
new_vaccinations numeric,
rolling_people_vaccinated numeric
)

Insert into #percent_population_vaccinated
Select dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations
, SUM(CONVERT(int,vac.new_vaccinations)) OVER (Partition by dea.location Order by dea.location, dea.date) AS rolling_people_vaccinated
--, (rolling_people_vaccinated/population)*100
From COVID19PortfolioProject..CovidDeaths dea
Join COVID19PortfolioProject..CovidVaccinations vac
	On dea.location = vac.location
	and dea.date = vac.date
Where dea.continent is not null
-- Order by 2,3

Select *, (rolling_people_vaccinated/population)*100
From #percent_population_vaccinated




-- Creating view to store data for later visualizations

Create view percent_population_vaccinated AS
Select dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations
, SUM(CONVERT(int,vac.new_vaccinations)) OVER (Partition by dea.location Order by dea.location, dea.date) AS rolling_people_vaccinated
--, (rolling_people_vaccinated/population)*100
From COVID19PortfolioProject..CovidDeaths dea
Join COVID19PortfolioProject..CovidVaccinations vac
	On dea.location = vac.location
	and dea.date = vac.date
Where dea.continent is not null
-- Order by 2,3


Select *
From percent_population_vaccinated
