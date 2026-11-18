-- =====================================================================
-- FoodRush · 01 · Catálogo, esquemas y volumen en Unity Catalog
-- Ejecutar en un notebook SQL o en el editor SQL del workspace.
-- =====================================================================

-- Catálogo del proyecto (objetos administrados por Unity Catalog)
CREATE CATALOG IF NOT EXISTS foodrush
  COMMENT 'Proyecto final DP-750: plataforma de pedidos a domicilio';

USE CATALOG foodrush;

-- Una capa por esquema (arquitectura Medallion)
CREATE SCHEMA IF NOT EXISTS bronze COMMENT 'Datos tal como llegan de origen, sin modificar';
CREATE SCHEMA IF NOT EXISTS silver COMMENT 'Datos limpios, validados y deduplicados';
CREATE SCHEMA IF NOT EXISTS gold   COMMENT 'Modelo estrella y data marts para consumo';

-- Volumen administrado donde se suben los ficheros de cada carga:
--   /Volumes/foodrush/bronze/landing/carga_1/
--   /Volumes/foodrush/bronze/landing/carga_2/
CREATE VOLUME IF NOT EXISTS bronze.landing
  COMMENT 'Zona de aterrizaje de ficheros CSV y JSON';

-- Comprobación
SHOW SCHEMAS IN foodrush;
SHOW VOLUMES IN foodrush.bronze;
