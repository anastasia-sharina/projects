Select *
From PortfolioProject..NashvilleHousing
Order by 2


-- Standardizing Date Format

Select SaleDateConverted, CONVERT(Date,SaleDate)
From PortfolioProject..NashvilleHousing

Update NashvilleHousing
SET SaleDate = CONVERT(Date,SaleDate)

ALTER TABLE NashvilleHousing
Add SaleDateConverted Date;

ALTER TABLE NashvilleHousing DROP COLUMN SaleDateConverted2
ALTER TABLE NashvilleHousing DROP COLUMN SaleDate2
ALTER TABLE NashvilleHousing DROP COLUMN SaleDateConverted1

Update NashvilleHousing
SET SaleDateConverted = CONVERT(Date,SaleDate)


-- Populating Property Address Data

Select *
From PortfolioProject..NashvilleHousing
--Where PropertyAddress is null
Order by ParcelID

Select a.ParcelID, a.PropertyAddress, b.ParcelID, b.PropertyAddress, ISNULL(a.PropertyAddress,b.PropertyAddress)
From PortfolioProject..NashvilleHousing a
JOIN PortfolioProject..NashvilleHousing b
	On a.ParcelID = b.ParcelID
	AND a.[UniqueID ] <> b.[UniqueID ]
Where a.PropertyAddress is null

Update a
Set PropertyAddress = ISNULL( a.PropertyAddress,b.PropertyAddress)
From PortfolioProject..NashvilleHousing a
JOIN PortfolioProject..NashvilleHousing b
	On a.ParcelID = b.ParcelID
	AND a.[UniqueID ] <> b.[UniqueID ]
Where a.PropertyAddress is null


-- Breaking out Address into Individual Columns (Address, City, State)

Select PropertyAddress
From PortfolioProject..NashvilleHousing
--Where PropertyAddress is null
--Order by ParcelID

Select
Substring(PropertyAddress, 1, Charindex(',', PropertyAddress) -1) as Address
, Substring(PropertyAddress, Charindex(',', PropertyAddress) +1, Len(PropertyAddress)) as Address
From PortfolioProject..NashvilleHousing


ALTER TABLE NashvilleHousing
Add PropertySplitAddress Nvarchar(255);

Update NashvilleHousing
SET PropertySplitAddress = Substring(PropertyAddress, 1, Charindex(',', PropertyAddress) -1)

ALTER TABLE NashvilleHousing
Add PropertySplitCity Nvarchar(255);


Update NashvilleHousing
SET PropertySplitCity = Substring(PropertyAddress, Charindex(',', PropertyAddress) +1, Len(PropertyAddress))

Select *
From PortfolioProject..NashvilleHousing



Select OwnerAddress
From PortfolioProject..NashvilleHousing

Select
Parsename(Replace(OwnerAddress, ',', '.') , 3)
,Parsename(Replace(OwnerAddress, ',', '.') , 2)
,Parsename(Replace(OwnerAddress, ',', '.') , 1)
From PortfolioProject..NashvilleHousing




ALTER TABLE NashvilleHousing
Add OwnerSplitAddress Nvarchar(255);

Update NashvilleHousing
SET OwnerSplitAddress = Parsename(Replace(OwnerAddress, ',', '.') , 3)

ALTER TABLE NashvilleHousing
Add OwnerSplitCity Nvarchar(255);

Update NashvilleHousing
SET OwnerSplitCity = Parsename(Replace(OwnerAddress, ',', '.') , 2)

ALTER TABLE NashvilleHousing
Add OwnerSplitState Nvarchar(255);

Update NashvilleHousing
SET OwnerSplitState = Parsename(Replace(OwnerAddress, ',', '.') , 1)



Select *
From PortfolioProject..NashvilleHousing



-- Changing E and N to Yes and No in "Sold as Vacant" field

Select Distinct (SoldAsVacant), Count(SoldAsVacant)
From PortfolioProject..NashvilleHousing
Group by SoldAsVacant
Order by 2

Select SoldAsVacant
, CASE When SoldAsVacant = 'Y' THEN 'Yes'
		When SoldAsVacant = 'N' THEN 'No'
		ELSE SoldAsVacant
		END
From PortfolioProject..NashvilleHousing

Update NashvilleHousing
SET SoldAsVacant = CASE When SoldAsVacant = 'Y' THEN 'Yes'
		When SoldAsVacant = 'N' THEN 'No'
		ELSE SoldAsVacant
		END


-- Removing Duplicates

Select *,
	ROW_NUMBER() OVER ( 
	PARTITION BY ParcelID,
				PropertyAddress,
				SalePrice,
				SaleDate,
				LegalReference
				ORDER BY
					UniqueID
					) row_num


From PortfolioProject.dbo.NashvilleHousing
Order by ParcelID

Select *
From PortfolioProject..NashvilleHousing
Order by 2