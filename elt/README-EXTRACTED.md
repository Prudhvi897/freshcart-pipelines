# FreshCart ELT source extracted from course notebook

These files were generated from `freshcart_elt_colab (1).ipynb` in the supplied course ZIP.

## Files
- `mock_data.py`, `extract.py`: mock API data and raw landing extraction
- `snowflake_io.py`: Snowflake connection, file loading, and SQL execution helpers
- `run_pipeline.py`: pipeline runner
- `sql/00_setup.sql`: database/schema/table setup
- `sql/10_silver_orders_clean.sql`: cleaning and quarantine
- `sql/20_silver_orders_dedup.sql`: deduplication
- `sql/30_dim_customers_scd2.sql`: customer tier history
- `sql/31_ref_fx_daily.sql`, `sql/32_ref_pincode_geo.sql`: reference data
- `sql/40_gold_fct_orders.sql`: gold fact table

## Important security note
The original notebook contains a plaintext Snowflake password in a setup cell. That cell is deliberately NOT included in this extracted source folder. Treat the password as exposed: change/rotate it in Snowflake immediately. Configure credentials through environment variables or a secrets manager; never commit them.
