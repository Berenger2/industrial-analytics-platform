-- Demonstration data for the fictional multi-site manufacturing platform.
-- Business keys and ON CONFLICT clauses make this script idempotent.

BEGIN;

INSERT INTO analytics.dim_sites (
    site_code,
    site_name,
    country_code,
    city,
    timezone,
    status,
    commissioned_on
)
VALUES
    (
        'FR-LYO',
        'Lyon Advanced Manufacturing',
        'FR',
        'Lyon',
        'Europe/Paris',
        'active',
        DATE '2014-09-15'
    ),
    (
        'DE-STU',
        'Stuttgart Precision Plant',
        'DE',
        'Stuttgart',
        'Europe/Berlin',
        'active',
        DATE '2011-03-21'
    ),
    (
        'ES-BIL',
        'Bilbao Assembly Center',
        'ES',
        'Bilbao',
        'Europe/Madrid',
        'maintenance',
        DATE '2018-06-04'
    )
ON CONFLICT (site_code) DO NOTHING;

INSERT INTO analytics.dim_products (
    product_code,
    product_name,
    product_family,
    unit_of_measure,
    standard_cycle_time_seconds,
    target_scrap_rate
)
VALUES
    ('DRV-X100', 'X100 Variable Speed Drive', 'Industrial Drives', 'unit', 84, 1.50),
    ('SNS-T450', 'T450 Temperature Sensor', 'Industrial Sensors', 'unit', 42, 0.80),
    ('CTL-M800', 'M800 Motion Controller', 'Control Systems', 'unit', 135, 2.00)
ON CONFLICT (product_code) DO NOTHING;

-- Resolve foreign keys from stable business codes instead of generated IDs.
INSERT INTO analytics.fact_production_orders (
    order_number,
    site_id,
    product_id,
    line_code,
    order_status,
    planned_quantity,
    produced_quantity,
    rejected_quantity,
    planned_start_at,
    planned_end_at,
    actual_start_at,
    actual_end_at
)
SELECT
    demo.order_number,
    site.site_id,
    product.product_id,
    demo.line_code,
    demo.order_status,
    demo.planned_quantity,
    demo.produced_quantity,
    demo.rejected_quantity,
    demo.planned_start_at,
    demo.planned_end_at,
    demo.actual_start_at,
    demo.actual_end_at
FROM (
    VALUES
        (
            'PO-2026-0501-LYO',
            'FR-LYO',
            'DRV-X100',
            'LINE-A2',
            'completed',
            1200,
            1192,
            14,
            TIMESTAMPTZ '2026-05-04 06:00:00+02',
            TIMESTAMPTZ '2026-05-05 14:00:00+02',
            TIMESTAMPTZ '2026-05-04 06:12:00+02',
            TIMESTAMPTZ '2026-05-05 13:41:00+02'
        ),
        (
            'PO-2026-0518-STU',
            'DE-STU',
            'CTL-M800',
            'CELL-C1',
            'completed',
            480,
            474,
            9,
            TIMESTAMPTZ '2026-05-18 05:30:00+02',
            TIMESTAMPTZ '2026-05-19 18:00:00+02',
            TIMESTAMPTZ '2026-05-18 05:28:00+02',
            TIMESTAMPTZ '2026-05-19 17:52:00+02'
        ),
        (
            'PO-2026-0608-BIL',
            'ES-BIL',
            'SNS-T450',
            'LINE-B4',
            'in_progress',
            2500,
            1640,
            11,
            TIMESTAMPTZ '2026-06-08 07:00:00+02',
            TIMESTAMPTZ '2026-06-10 15:00:00+02',
            TIMESTAMPTZ '2026-06-08 07:16:00+02',
            NULL::TIMESTAMPTZ
        ),
        (
            'PO-2026-0616-LYO',
            'FR-LYO',
            'SNS-T450',
            'LINE-A1',
            'planned',
            3000,
            0,
            0,
            TIMESTAMPTZ '2026-06-16 06:00:00+02',
            TIMESTAMPTZ '2026-06-18 14:00:00+02',
            NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ
        )
) AS demo (
    order_number,
    site_code,
    product_code,
    line_code,
    order_status,
    planned_quantity,
    produced_quantity,
    rejected_quantity,
    planned_start_at,
    planned_end_at,
    actual_start_at,
    actual_end_at
)
JOIN analytics.dim_sites AS site
    ON site.site_code = demo.site_code
JOIN analytics.dim_products AS product
    ON product.product_code = demo.product_code
ON CONFLICT (order_number) DO NOTHING;

INSERT INTO analytics.fact_quality_controls (
    control_reference,
    production_order_id,
    controlled_at,
    sample_size,
    passed_quantity,
    failed_quantity,
    result,
    defect_category,
    inspector_name,
    notes
)
SELECT
    demo.control_reference,
    production_order.production_order_id,
    demo.controlled_at,
    demo.sample_size,
    demo.passed_quantity,
    demo.failed_quantity,
    demo.result,
    demo.defect_category,
    demo.inspector_name,
    demo.notes
FROM (
    VALUES
        (
            'QC-LYO-2026-0505-01',
            'PO-2026-0501-LYO',
            TIMESTAMPTZ '2026-05-05 10:30:00+02',
            80,
            79,
            1,
            'passed',
            'Surface finish',
            'Claire Bernard',
            'One cosmetic defect; functional tests passed.'
        ),
        (
            'QC-STU-2026-0519-02',
            'PO-2026-0518-STU',
            TIMESTAMPTZ '2026-05-19 15:15:00+02',
            50,
            47,
            3,
            'warning',
            'Connector alignment',
            'Jonas Keller',
            'Additional end-of-line inspection requested.'
        ),
        (
            'QC-BIL-2026-0609-01',
            'PO-2026-0608-BIL',
            TIMESTAMPTZ '2026-06-09 11:45:00+02',
            120,
            120,
            0,
            'passed',
            NULL,
            'Marta Etxeberria',
            'Dimensions and calibration within specification.'
        )
) AS demo (
    control_reference,
    order_number,
    controlled_at,
    sample_size,
    passed_quantity,
    failed_quantity,
    result,
    defect_category,
    inspector_name,
    notes
)
JOIN analytics.fact_production_orders AS production_order
    ON production_order.order_number = demo.order_number
ON CONFLICT (control_reference) DO NOTHING;

INSERT INTO analytics.import_logs (
    import_reference,
    source_system,
    source_file,
    import_status,
    rows_received,
    rows_processed,
    rows_rejected,
    started_at,
    completed_at,
    error_message
)
VALUES
    (
        'IMP-MES-LYO-20260505-01',
        'Lyon MES',
        'production_orders_2026-05-05.csv',
        'completed',
        1250,
        1250,
        0,
        TIMESTAMPTZ '2026-05-05 23:05:00+02',
        TIMESTAMPTZ '2026-05-05 23:05:18+02',
        NULL
    ),
    (
        'IMP-QMS-STU-20260519-01',
        'Stuttgart QMS',
        'quality_controls_2026-05-19.csv',
        'partial',
        512,
        509,
        3,
        TIMESTAMPTZ '2026-05-19 22:30:00+02',
        TIMESTAMPTZ '2026-05-19 22:30:09+02',
        'Three rows rejected because the order number was unknown.'
    ),
    (
        'IMP-ERP-GLOBAL-20260610-01',
        'Corporate ERP',
        NULL,
        'running',
        840,
        620,
        0,
        TIMESTAMPTZ '2026-06-10 04:00:00+00',
        NULL,
        NULL
    )
ON CONFLICT (import_reference) DO NOTHING;

COMMIT;
