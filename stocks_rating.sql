----------------------TABLES--------------------------------
DROP TABLE `latest_results`;
CREATE TABLE `latest_results` (
  `Name` text,
  `BSE Code` double DEFAULT NULL,
  `NSE Code` text,
  `Industry` text,
  `Current Price` double DEFAULT NULL,
  `Market Capitalization` double DEFAULT NULL,
  `Market Cap` text,
  `Promoter holding` double DEFAULT NULL,
  `Price to Earning` double DEFAULT NULL,
  `Industry PE` double DEFAULT NULL,
  `PEG Ratio` double DEFAULT NULL,
  `Return over 1week` double DEFAULT NULL,
  `Return over 1month` double DEFAULT NULL,
  `Return over 3months` double DEFAULT NULL,
  `Return over 6months` double DEFAULT NULL,
  `EPS latest quarter` double DEFAULT NULL,
  `EPS preceding quarter` double DEFAULT NULL,
  `EPS preceding year quarter` double DEFAULT NULL,
  `Debt` double DEFAULT NULL,
  `Debt to equity` double DEFAULT NULL,
  `OPM latest quarter` double DEFAULT NULL,
  `OPM preceding quarter` double DEFAULT NULL,
  `Return on equity` double DEFAULT NULL,
  `Return on capital employed` double DEFAULT NULL,
  `Price to book value` double DEFAULT NULL,
  `FII holding` double DEFAULT NULL,
  `DII holding` double DEFAULT NULL,
  `Public holding` double DEFAULT NULL,
  `Last result date` double DEFAULT NULL,
  `screener` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE `screeners`;
CREATE TABLE `screeners` (
  `Name` varchar(200) DEFAULT NULL,
  `BSE Code` varchar(20) DEFAULT NULL,
  `NSE Code` varchar(20) DEFAULT NULL,
  `Industry` varchar(200) DEFAULT NULL,
  `Current Price` varchar(20) DEFAULT NULL,
  `Market Capitalization` varchar(20) DEFAULT NULL,
  `Market Cap` text,
  `Promoter holding` varchar(20) DEFAULT NULL,
  `Price to Earning` varchar(20) DEFAULT NULL,
  `Industry PE` varchar(20) DEFAULT NULL,
  `PEG Ratio` double DEFAULT NULL,
  `Return over 1week` varchar(20) DEFAULT NULL,
  `Return over 1month` varchar(20) DEFAULT NULL,
  `Return over 3months` varchar(20) DEFAULT NULL,
  `Return over 6months` varchar(20) DEFAULT NULL,
  `EPS latest quarter` varchar(20) DEFAULT NULL,
  `EPS preceding quarter` varchar(20) DEFAULT NULL,
  `EPS preceding year quarter` varchar(20) DEFAULT NULL,
  `Debt` varchar(20) DEFAULT NULL,
  `Debt to equity` double DEFAULT NULL,
  `OPM latest quarter` varchar(20) DEFAULT NULL,
  `OPM preceding quarter` varchar(20) DEFAULT NULL,
  `Return on equity` varchar(20) DEFAULT NULL,
  `Return on capital employed` varchar(20) DEFAULT NULL,
  `Price to book value` varchar(20) DEFAULT NULL,
  `FII holding` varchar(20) DEFAULT NULL,
  `DII holding` varchar(20) DEFAULT NULL,
  `Public holding` varchar(20) DEFAULT NULL,
  `screener` varchar(200) DEFAULT NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE `mc_technicals`;
CREATE TABLE `mc_technicals` (
  `Name` text,
  `BSE Code` double DEFAULT NULL,
  `NSE Code` text,
  `mc essentials` int DEFAULT NULL,
  `mc technicals` text,
  `updated_date` text,
  `screener` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE mstock_margin;
CREATE TABLE `mstock_margin` (
  `Company Name` varchar(250) DEFAULT NULL,
  `Symbol` varchar(20) DEFAULT NULL,
  `Margin` int DEFAULT NULL,
  `Max Funding` int DEFAULT NULL,
  `screener` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE `score_refactor`;
CREATE TABLE `score_refactor` (
  `Name` varchar(200) NOT NULL,
  `NSE Code` varchar(20) DEFAULT NULL,
  `BSE Code` varchar(20) DEFAULT NULL,
  `score_eps` int DEFAULT 0,
  `score_pe` int DEFAULT 0,
  `score_mc` int DEFAULT 0,
  `score_opm` int DEFAULT 0,
  `score_roe_roce` int DEFAULT 0,
  `score_public_holding` int DEFAULT 0,
  `score_returns` int DEFAULT 0,
  `Total Score` int DEFAULT 0,
  `screener` text

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

------------------------VIEWS-----------------------------------
DROP  VIEW `vw_latest_results`;
CREATE VIEW `vw_latest_results` AS
select
  `lr`.`Name` AS `Name`,
  `lr`.`BSE Code` AS `BSE Code`,
  `lr`.`NSE Code` AS `NSE Code`,
  `lr`.`Industry` AS `Industry`,
  `lr`.`Current Price` AS `Current Price`,
  `lr`.`Market Capitalization` AS `Market Capitalization`,
  `lr`.`Market Cap` AS `Market Cap`,
  `lr`.`Promoter holding` AS `Promoter holding`,
  `lr`.`Price to Earning` AS `Price to Earning`,
  `lr`.`Industry PE` AS `Industry PE`,
  `lr`.`PEG Ratio` as `PEG Ratio`,
  `lr`.`Return over 1week` AS `Return over 1week`,
  `lr`.`Return over 1month` AS `Return over 1month`,
  `lr`.`Return over 3months` AS `Return over 3months`,
  `lr`.`Return over 6months` AS `Return over 6months`,
  `lr`.`EPS latest quarter` AS `EPS latest quarter`,
  `lr`.`EPS preceding quarter` AS `EPS preceding quarter`,
  `lr`.`EPS preceding year quarter` AS `EPS preceding year quarter`,
  `lr`.`Debt` AS `Debt`,
  `lr`.`Debt to equity` as `Debt to equity`,
  `lr`.`OPM latest quarter` AS `OPM latest quarter`,
  `lr`.`OPM preceding quarter` AS `OPM preceding quarter`,
  `lr`.`Return on equity` AS `Return on equity`,
  `lr`.`Return on capital employed` AS `Return on capital employed`,
  `lr`.`Price to book value` AS `Price to book value`,
  `lr`.`FII holding` AS `FII holding`,
  `lr`.`DII holding` AS `DII holding`,
  `lr`.`Public holding` AS `Public holding`,
  `lr`.`Last result date` AS `Last result date`,
  `lr`.`screener` AS `screener`,
  `mct`.`mc essentials` AS `mc essentials`,
  `mct`.`mc technicals` AS `mc technicals`,
  `mm`.`Margin` AS `Margin`,
  `sr`.`Total Score` AS `Total Score`
from `latest_results` `lr`
left join `mc_technicals` `mct` on `lr`.`Name` = `mct`.`Name`
left join `mstock_margin` `mm` on `lr`.`NSE Code`=`mm`.`Symbol`
left join `score_refactor` `sr` on `lr`.`Name`=`sr`.`Name` ;


DROP   VIEW vw_screeners;
CREATE VIEW `vw_screeners` AS
select
  `scr`.`Name` AS `Name`,
  `scr`.`BSE Code` AS `BSE Code`,
  `scr`.`NSE Code` AS `NSE Code`,
  `scr`.`Industry` AS `Industry`,
  `scr`.`Current Price` AS `Current Price`,
  `scr`.`Market Capitalization` AS `Market Capitalization`,
  `scr`.`Market Cap` AS `Market Cap`,
  `scr`.`Promoter holding` AS `Promoter holding`,
  `scr`.`Price to Earning` AS `Price to Earning`,
  `scr`.`Industry PE` AS `Industry PE`,
  `scr`.`PEG Ratio` as `PEG Ratio`,
  `scr`.`Return over 1week` AS `Return over 1week`,
  `scr`.`Return over 1month` AS `Return over 1month`,
  `scr`.`Return over 3months` AS `Return over 3months`,
  `scr`.`Return over 6months` AS `Return over 6months`,
  `scr`.`EPS latest quarter` AS `EPS latest quarter`,
  `scr`.`EPS preceding quarter` AS `EPS preceding quarter`,
  `scr`.`EPS preceding year quarter` AS `EPS preceding year quarter`,
  `scr`.`Debt` AS `Debt`,
  `scr`.`Debt to equity` as `Debt to equity`,
  `scr`.`OPM latest quarter` AS `OPM latest quarter`,
  `scr`.`OPM preceding quarter` AS `OPM preceding quarter`,
  `scr`.`Return on equity` AS `Return on equity`,
  `scr`.`Return on capital employed` AS `Return on capital employed`,
  `scr`.`Price to book value` AS `Price to book value`,
  `scr`.`FII holding` AS `FII holding`,
  `scr`.`DII holding` AS `DII holding`,
  `scr`.`Public holding` AS `Public holding`,
  `scr`.`screener` AS `screener`,
  `mct`.`mc essentials` AS `mc essentials`,
  `mct`.`mc technicals` AS `mc technicals`,
  `mm`.`Margin` AS `Margin` ,
  `sr`.`Total Score` AS `Total Score`
from `screeners` `scr`
left join `mc_technicals` `mct` on `scr`.`Name` = `mct`.`Name`
left join `mstock_margin` `mm` on `scr`.`NSE Code`=`mm`.`Symbol`
left join `score_refactor` `sr` on `scr`.`Name`=`sr`.`Name` ;


DROP VIEW vw_quality_stocks;
CREATE VIEW `vw_quality_stocks` AS
select
  `lr`.`Name` AS `Name`,
  `lr`.`BSE Code` AS `BSE Code`,
  `lr`.`NSE Code` AS `NSE Code`,
  `lr`.`Industry` AS `Industry`,
  `lr`.`Current Price` AS `Current Price`,
  `lr`.`Market Capitalization` AS `Market Capitalization`,
  `lr`.`Market Cap` AS `Market Cap`,
  `lr`.`EPS latest quarter` AS `EPS latest quarter`,
  `lr`.`EPS preceding quarter` AS `EPS preceding quarter`,
  `lr`.`EPS preceding year quarter` AS `EPS preceding year quarter`,
  `lr`.`Return on equity` AS `Return on equity`,
  `lr`.`Return on capital employed` AS `Return on capital employed`,
  `lr`.`Price to Earning` AS `Price to Earning`,
  `lr`.`Industry PE` AS `Industry PE`,
  `lr`.`PEG Ratio` AS `PEG Ratio`,
  `lr`.`Debt` AS `Debt`,
  `lr`.`Debt to equity` AS `Debt to equity`,
  `lr`.`OPM latest quarter` AS `OPM latest quarter`,
  `lr`.`OPM preceding quarter` AS `OPM preceding quarter`,
  `lr`.`Price to book value` AS `Price to book value`,
  `lr`.`Promoter holding` AS `Promoter holding`,
  `lr`.`FII holding` AS `FII holding`,
  `lr`.`DII holding` AS `DII holding`,
  `lr`.`Public holding` AS `Public holding`,
  `lr`.`Return over 1week` AS `Return over 1week`,
  `lr`.`Return over 1month` AS `Return over 1month`,
  `lr`.`Return over 3months` AS `Return over 3months`,
  `lr`.`Return over 6months` AS `Return over 6months`,
  `lr`.`Last result date` AS `Last result date`,
  `lr`.`screener` AS `screener`,
  `mct`.`mc essentials` AS `mc essentials`,
  `mct`.`mc technicals` AS `mc technicals`,
  `mm`.`Margin` AS `Margin` ,
  `sr`.`Total Score` AS `Total Score`
from `latest_results` `lr`
left join `mc_technicals` `mct` on `lr`.`Name` = `mct`.`Name`
left join `mstock_margin` `mm` on `lr`.`NSE Code` = `mm`.`Symbol`
left join `score_refactor` `sr` on `lr`.`Name`=`sr`.`Name`
where `lr`.`Market Capitalization` > 1000 and `lr`.`Promoter holding` > 50 and
(`lr`.`EPS latest quarter` > `lr`.`EPS preceding quarter` and `lr`.`EPS latest quarter` > `lr`.`EPS preceding year quarter`)
and (`lr`.`Return on equity` > 15)     and (      `lr`.`Return on capital employed` > 15    )
order by   `lr`.`Market Capitalization` desc;


DROP   VIEW vw_my_holdings;
CREATE VIEW `vw_my_holdings` AS
select
  `my_holdings`.`holding_id` AS `holding_id`,
  `my_holdings`.`Company_Name` AS `Company_Name`,
  `my_holdings`.`Buy_Qty` AS `Buy_Qty`,
  `my_holdings`.`Buy_Price` AS `Buy_Price`,
  `my_holdings`.`Buy_Date` AS `Buy_Date`,
  `my_holdings`.`Sell_Qty` AS `Sell_Qty`,
  `my_holdings`.`Sell_Price` AS `Sell_Price`,
  `my_holdings`.`Sell_Date` AS `Sell_Date`,
  `my_holdings`.`Basket_ID` AS `Basket_ID`,
  `company_list`.`NSE_Code` AS `NSE_Code`,
  `company_list`.`BSE_Code` AS `BSE_Code`,
  `company_list`.`Industry` AS `Industry` ,
  `sr`.`Total Score` AS `Total Score`
from `my_holdings`
join `company_list` on `my_holdings`.`Company_Name` = `company_list`.`Name`
left join `latest_results` on  `my_holdings`.`Company_Name` = `latest_results`.`Name`
left join `score_refactor` `sr` on `my_holdings`.`Company_Name`=`sr`.`Name`
