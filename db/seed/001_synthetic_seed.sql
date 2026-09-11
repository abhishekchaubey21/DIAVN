-- ============================================================================
-- DIAVN Database Seed Data: 001_synthetic_seed.sql
-- Project: Dealer Integrity & Asset Verification Network (DIAVN)
-- Synthetic Dataset for Local Development & Testing
-- NOTE: All names, numbers, GSTINs, addresses, and serials are purely SYNTHETIC.
-- ============================================================================

-- Clean existing data in dependency order
TRUNCATE TABLE audit_log, verification_tasks, entity_relationships, risk_scores,
               risk_signals, registered_assets, product_price_benchmarks,
               installation_images, invoice_line_items, invoices, cases,
               customers, dealers, users CASCADE;

-- ----------------------------------------------------------------------------
-- 1. USERS
-- ----------------------------------------------------------------------------
INSERT INTO users (id, email, full_name, role) VALUES
('11111111-1111-1111-1111-111111111101', 'risk.officer1@diavn.synthetic', 'Arun Swaminathan (Synthetic User)', 'risk_officer'),
('11111111-1111-1111-1111-111111111102', 'lead.auditor@diavn.synthetic', 'Pooja Bannerjee (Synthetic User)', 'auditor'),
('11111111-1111-1111-1111-111111111103', 'field.verifier@diavn.synthetic', 'Kiran Rathore (Synthetic User)', 'field_agent');

-- ----------------------------------------------------------------------------
-- 2. DEALERS (3 Synthetic Dealers)
-- ----------------------------------------------------------------------------
INSERT INTO dealers (id, dealer_code, name, business_name, gstin, pan, cin, address, city, state, pincode, contact_email, contact_phone, status, risk_tier) VALUES
('22222222-2222-2222-2222-222222222201', 'DLR-APX-01', 'Apex Solar Equipment Pvt Ltd', 'Apex Solar Solutions', '27AAACA1234A1Z5', 'AAACA1234A', 'U40106MH2018PTC309812', 'Plot 45, MIDC Phase II, Bhosari', 'Pune', 'Maharashtra', '411019', 'compliance@apexsolar.synthetic', '+91-9823000001', 'active', 'low'),
('22222222-2222-2222-2222-222222222202', 'DLR-SUN-02', 'SunPower Retail & Infra Solutions', 'SunPower Infra', '24BBBCB5678B1Z2', 'BBBCB5678B', 'U40300GJ2020PTC412098', '12, Commercial Hub, Ring Road', 'Surat', 'Gujarat', '395002', 'accounts@sunpowerinfra.synthetic', '+91-9823000002', 'under_review', 'medium'),
('22222222-2222-2222-2222-222222222203', 'DLR-RAD-03', 'Radiant AgroTech Distributions', 'Radiant Agro Dist', '29CCCC09876C1Z9', 'CCCC09876C', 'U01100KA2022PTC567432', '88, Agro Yard Extension, Hebbal', 'Bengaluru', 'Karnataka', '560024', 'ops@radiantagrotech.synthetic', '+91-9823000003', 'flagged', 'high');

-- ----------------------------------------------------------------------------
-- 3. CUSTOMERS (5 Synthetic Borrowers/Customers)
-- ----------------------------------------------------------------------------
INSERT INTO customers (id, customer_code, full_name, contact_phone, contact_email, address, city, state, pincode, id_proof_type, id_proof_number_hash) VALUES
('33333333-3333-3333-3333-333333333301', 'CUST-001', 'Rajesh Sharma (Synthetic)', '+91-9800000001', 'rajesh.sharma@example.synthetic', 'Village Khed, Taluka Shirur', 'Pune', 'Maharashtra', '412218', 'AADHAAR_SYNTHETIC', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
('33333333-3333-3333-3333-333333333302', 'CUST-002', 'Meera Patel (Synthetic)', '+91-9800000002', 'meera.patel@example.synthetic', 'Farm 4A, Bardoli Road', 'Surat', 'Gujarat', '394601', 'AADHAAR_SYNTHETIC', 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb'),
('33333333-3333-3333-3333-333333333303', 'CUST-003', 'GreenFields Agri Enterprises', '+91-9800000003', 'billing@greenfields.synthetic', 'Sy 102/4, Devanahalli Rural', 'Bengaluru Rural', 'Karnataka', '562110', 'PAN_SYNTHETIC', '4e1243bd22c66e76c2ba9eddc1f91394e57f9f835c9cd0c82de19245578a49ee'),
('33333333-3333-3333-3333-333333333304', 'CUST-004', 'Vikas Deshmukh (Synthetic)', '+91-9800000004', 'vikas.deshmukh@example.synthetic', 'Survey 52, Baramati Farm Sector', 'Baramati', 'Maharashtra', '413102', 'AADHAAR_SYNTHETIC', '8f434346648f6b96df89dda901c5176b10e6d059612d556b925c07b747c97357'),
('33333333-3333-3333-3333-333333333305', 'CUST-005', 'Anita Sundaram (Synthetic)', '+91-9800000005', 'anita.sundaram@example.synthetic', 'Plot 18, Hosur Industrial Border', 'Bengaluru', 'Karnataka', '560100', 'AADHAAR_SYNTHETIC', 'fe2592b42a727e977f055947385b709cc82b16b9a87f88c6abf3900d65d013e8');

-- ----------------------------------------------------------------------------
-- 4. PRODUCT PRICE BENCHMARKS (5+ Benchmarks)
-- ----------------------------------------------------------------------------
INSERT INTO product_price_benchmarks (id, asset_category, brand, model_name, specifications, benchmark_min_price, benchmark_max_price, benchmark_avg_price, currency, effective_from) VALUES
('44444444-4444-4444-4444-444444444401', 'Solar Inverter', 'SunGuard', 'SG-5KVA-HYBRID', '5kVA 48V Hybrid Solar Inverter with MPPT', 45000.00, 58000.00, 52000.00, 'INR', '2026-01-01'),
('44444444-4444-4444-4444-444444444402', 'Solar Water Pump', 'AquaSun', 'ASP-5HP-SUB-V4', '5HP 3-Phase AC Submersible Solar Water Pump', 160000.00, 210000.00, 185000.00, 'INR', '2026-01-01'),
('44444444-4444-4444-4444-444444444403', 'Solar PV Panel', 'LumiSolar', 'LS-540W-MONO-PERC', '540W Monocrystalline PERC Half-cut Panel', 11500.00, 15000.00, 13200.00, 'INR', '2026-01-01'),
('44444444-4444-4444-4444-444444444404', 'Solar Inverter', 'VoltMax', 'VM-10KW-COMM', '10kW Grid-Tie 3-Phase Commercial Inverter', 85000.00, 110000.00, 98000.00, 'INR', '2026-01-01'),
('44444444-4444-4444-4444-444444444405', 'Micro-Irrigation Controller', 'AgroSense', 'ASC-AUTO-V3', 'IoT Automated Precision Drip Controller', 28000.00, 36000.00, 32000.00, 'INR', '2026-01-01'),
('44444444-4444-4444-4444-444444444406', 'Energy Storage', 'PowerCell', 'PC-LFP-48V-100AH', '4.8kWh Lithium Iron Phosphate Battery Bank', 95000.00, 125000.00, 110000.00, 'INR', '2026-01-01');

-- ----------------------------------------------------------------------------
-- 5. CASES (10 Synthetic Cases covering scenarios)
-- Scenario 1: Clean / Normal (Cases 001, 002)
-- Scenario 2: Inflated Price (Cases 003, 004)
-- Scenario 3: Duplicate Serial Number (Cases 005, 006)
-- Scenario 4: Suspicious Dealer Relationship (Cases 007, 008)
-- Additional Test Cases: 009 (Pending Verification), 010 (Field Visit Scheduled)
-- ----------------------------------------------------------------------------
INSERT INTO cases (id, case_number, dealer_id, customer_id, asset_type, claimed_installation_address, claimed_lat, claimed_lng, loan_amount, status, risk_level, notes) VALUES
-- Case 1: Clean Normal
('55555555-5555-5555-5555-555555555501', 'CAS-2026-001', '22222222-2222-2222-2222-222222222201', '33333333-3333-3333-3333-333333333301', 'Solar Water Pump 5HP', 'Plot 12, Farm Sector B, Shirur, Pune, Maharashtra', 18.8256000, 74.3789000, 195000.00, 'verified', 'low', 'Standard clean installation. All serials and invoice matched benchmarks.'),
-- Case 2: Clean Normal
('55555555-5555-5555-5555-555555555502', 'CAS-2026-002', '22222222-2222-2222-2222-222222222201', '33333333-3333-3333-3333-333333333304', 'Solar Inverter 5kVA', 'Survey 52, Baramati Farm Sector, Baramati, Maharashtra', 18.1523000, 74.5768000, 55000.00, 'verified', 'low', 'Verified against manufacturer database and benchmark pricing.'),
-- Case 3: Inflated-Price Case
('55555555-5555-5555-5555-555555555503', 'CAS-2026-003', '22222222-2222-2222-2222-222222222202', '33333333-3333-3333-3333-333333333302', 'Solar Inverter 5kVA', 'Farm 4A, Bardoli Road, Surat, Gujarat', 21.1189000, 73.1145000, 115000.00, 'under_review', 'high', 'Invoice unit rate (115,000 INR) is +121% over category benchmark avg (52,000 INR).'),
-- Case 4: Inflated-Price Case
('55555555-5555-5555-5555-555555555504', 'CAS-2026-004', '22222222-2222-2222-2222-222222222202', '33333333-3333-3333-3333-333333333302', 'Solar PV Panel System 5kW', 'Farm 4B, Bardoli Road, Surat, Gujarat', 21.1192000, 73.1150000, 390000.00, 'flagged', 'high', 'Disproportionate invoice total for standard mono PERC modules.'),
-- Case 5: Duplicate-Serial Case
('55555555-5555-5555-5555-555555555505', 'CAS-2026-005', '22222222-2222-2222-2222-222222222203', '33333333-3333-3333-3333-333333333303', 'Solar Water Pump 5HP', 'Sy 102/4, Devanahalli Rural, Bengaluru Rural, Karnataka', 13.2489000, 77.7123000, 190000.00, 'flagged', 'critical', 'Pump serial ASP-2025-99881 was previously registered in active case CAS-2025-8812 in Pune.'),
-- Case 6: Duplicate-Serial Case
('55555555-5555-5555-5555-555555555506', 'CAS-2026-006', '22222222-2222-2222-2222-222222222203', '33333333-3333-3333-3333-333333333305', 'Solar Inverter 10kW', 'Plot 18, Hosur Industrial Border, Bengaluru, Karnataka', 12.7845000, 77.7890000, 105000.00, 'under_review', 'critical', 'Inverter serial VM-10KW-77441 matches asset currently registered in another financial institution network.'),
-- Case 7: Suspicious Dealer Relationship Case
('55555555-5555-5555-5555-555555555507', 'CAS-2026-007', '22222222-2222-2222-2222-222222222203', '33333333-3333-3333-3333-333333333303', 'Micro-Irrigation Controller', '88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka', 13.0358000, 77.5970000, 34000.00, 'flagged', 'high', 'Borrower claimed address is identical to dealer commercial registered address.'),
-- Case 8: Suspicious Dealer Relationship Case
('55555555-5555-5555-5555-555555555508', 'CAS-2026-008', '22222222-2222-2222-2222-222222222203', '33333333-3333-3333-3333-333333333305', 'Solar Inverter 5kVA', '88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka', 13.0358000, 77.5970000, 56000.00, 'flagged', 'high', 'Customer contact phone shares identical digit cluster with dealer director registered phone.'),
-- Case 9: Pending Verification Case
('55555555-5555-5555-5555-555555555509', 'CAS-2026-009', '22222222-2222-2222-2222-222222222201', '33333333-3333-3333-3333-333333333301', 'Energy Storage 4.8kWh', 'Plot 14, Farm Sector B, Shirur, Pune, Maharashtra', 18.8260000, 74.3792000, 115000.00, 'submitted', 'requires_verification', 'New submission awaiting multi-module pipeline execution.'),
-- Case 10: Field Visit Scheduled Case
('55555555-5555-5555-5555-555555555510', 'CAS-2026-010', '22222222-2222-2222-2222-222222222202', '33333333-3333-3333-3333-333333333304', 'Solar Water Pump 5HP', 'Survey 56, Baramati Farm Sector, Baramati, Maharashtra', 18.1530000, 74.5775000, 188000.00, 'verification_pending', 'medium', 'Geo-tag discrepancy between claimed address and EXIF telemetry requires physical verification.');

-- ----------------------------------------------------------------------------
-- 6. REGISTERED ASSETS (5+ Cross-case Registered Assets)
-- ----------------------------------------------------------------------------
INSERT INTO registered_assets (id, serial_number, asset_type, brand, model_name, original_dealer_id, original_case_id, installation_lat, installation_lng, installed_at, registration_status) VALUES
('66666666-6666-6666-6666-666666666601', 'ASP-2025-99881', 'Solar Water Pump 5HP', 'AquaSun', 'ASP-5HP-SUB-V4', '22222222-2222-2222-2222-222222222201', '55555555-5555-5555-5555-555555555501', 18.8256000, 74.3789000, '2025-08-14', 'active'),
('66666666-6666-6666-6666-666666666602', 'VM-10KW-77441', 'Solar Inverter 10kW', 'VoltMax', 'VM-10KW-COMM', '22222222-2222-2222-2222-222222222202', NULL, 21.1189000, 73.1145000, '2025-11-20', 'flagged_duplicate'),
('66666666-6666-6666-6666-666666666603', 'SG-5K-00192', 'Solar Inverter 5kVA', 'SunGuard', 'SG-5KVA-HYBRID', '22222222-2222-2222-2222-222222222201', '55555555-5555-5555-5555-555555555502', 18.1523000, 74.5768000, '2026-01-10', 'active'),
('66666666-6666-6666-6666-666666666604', 'LS-540-88310', 'Solar PV Panel', 'LumiSolar', 'LS-540W-MONO-PERC', '22222222-2222-2222-2222-222222222201', '55555555-5555-5555-5555-555555555502', 18.1523000, 74.5768000, '2026-01-10', 'active'),
('66666666-6666-6666-6666-666666666605', 'ASC-AUTO-4401', 'Micro-Irrigation Controller', 'AgroSense', 'ASC-AUTO-V3', '22222222-2222-2222-2222-222222222201', NULL, 18.8260000, 74.3792000, '2026-02-05', 'active'),
('66666666-6666-6666-6666-666666666606', 'PC-LFP-99021', 'Energy Storage 4.8kWh', 'PowerCell', 'PC-LFP-48V-100AH', '22222222-2222-2222-2222-222222222201', NULL, 18.8260000, 74.3792000, '2026-02-28', 'active');

-- ----------------------------------------------------------------------------
-- 7. INVOICES & LINE ITEMS
-- ----------------------------------------------------------------------------
INSERT INTO invoices (id, case_id, dealer_id, invoice_number, invoice_date, total_amount, tax_amount, file_path, status, verification_status, extracted_json, extraction_confidence) VALUES
('77777777-7777-7777-7777-777777777701', '55555555-5555-5555-5555-555555555501', '22222222-2222-2222-2222-222222222201', 'INV-APX-2026-081', '2026-01-12', 195000.00, 23400.00, 'synthetic_invoices/inv_apx_081.pdf', 'completed', 'verified', '{"invoice_number": "INV-APX-2026-081", "dealer_name": "Apex Solar Equipment Pvt Ltd", "total_amount": 195000.0}'::jsonb, 0.98),
('77777777-7777-7777-7777-777777777702', '55555555-5555-5555-5555-555555555503', '22222222-2222-2222-2222-222222222202', 'INV-SUN-2026-114', '2026-01-20', 115000.00, 13800.00, 'synthetic_invoices/inv_sun_114.pdf', 'completed', 'anomaly_detected', '{"invoice_number": "INV-SUN-2026-114", "dealer_name": "SunPower Retail & Infra", "total_amount": 115000.0}'::jsonb, 0.95),
('77777777-7777-7777-7777-777777777703', '55555555-5555-5555-5555-555555555505', '22222222-2222-2222-2222-222222222203', 'INV-RAD-2026-009', '2026-02-01', 190000.00, 22800.00, 'synthetic_invoices/inv_rad_009.pdf', 'completed', 'anomaly_detected', '{"invoice_number": "INV-RAD-2026-009", "dealer_name": "Radiant AgroTech", "total_amount": 190000.0}'::jsonb, 0.94),
('77777777-7777-7777-7777-777777777704', '55555555-5555-5555-5555-555555555507', '22222222-2222-2222-2222-222222222203', 'INV-RAD-2026-014', '2026-02-15', 34000.00, 4080.00, 'synthetic_invoices/inv_rad_014.pdf', 'completed', 'anomaly_detected', '{"invoice_number": "INV-RAD-2026-014", "dealer_name": "Radiant AgroTech", "total_amount": 34000.0}'::jsonb, 0.96);

INSERT INTO invoice_line_items (id, invoice_id, item_description, hsn_code, quantity, unit_price, total_amount, serial_numbers, benchmark_variance_pct) VALUES
('88888888-8888-8888-8888-888888888801', '77777777-7777-7777-7777-777777777701', 'AquaSun 5HP Solar Pump System', '84137010', 1.00, 195000.00, 195000.00, ARRAY['ASP-2025-99881'], 5.41),
('88888888-8888-8888-8888-888888888802', '77777777-7777-7777-7777-777777777702', 'SunGuard SG-5KVA Hybrid Inverter', '85044030', 1.00, 115000.00, 115000.00, ARRAY['SG-5K-99014'], 121.15),
('88888888-8888-8888-8888-888888888803', '77777777-7777-7777-7777-777777777703', 'AquaSun 5HP Solar Pump System', '84137010', 1.00, 190000.00, 190000.00, ARRAY['ASP-2025-99881'], 2.70),
('88888888-8888-8888-8888-888888888804', '77777777-7777-7777-7777-777777777704', 'AgroSense IoT Precision Drip Controller', '90328900', 1.00, 34000.00, 34000.00, ARRAY['ASC-AUTO-8812'], 6.25);

-- ----------------------------------------------------------------------------
-- 8. INSTALLATION IMAGES
-- ----------------------------------------------------------------------------
INSERT INTO installation_images (id, case_id, image_type, file_path, original_filename, file_size_bytes, phash, exif_lat, exif_lng, verification_status) VALUES
('99999999-9999-9999-9999-999999999901', '55555555-5555-5555-5555-555555555501', 'installation_wide', 'synthetic_images/case1_wide.jpg', 'img_site_wide.jpg', 245100, 'a1b2c3d4e5f60718', 18.8255900, 74.3789100, 'verified'),
('99999999-9999-9999-9999-999999999902', '55555555-5555-5555-5555-555555555501', 'nameplate', 'synthetic_images/case1_nameplate.jpg', 'img_nameplate_asp99881.jpg', 189400, 'b2c3d4e5f6a10829', 18.8255950, 74.3789050, 'verified'),
('99999999-9999-9999-9999-999999999903', '55555555-5555-5555-5555-555555555503', 'installation_wide', 'synthetic_images/case3_wide.jpg', 'img_inverter_wall.jpg', 312000, 'c3d4e5f6a1b20930', 21.1189000, 73.1145000, 'analyzed'),
('99999999-9999-9999-9999-999999999904', '55555555-5555-5555-5555-555555555505', 'nameplate', 'synthetic_images/case5_nameplate.jpg', 'img_duplicate_plate.jpg', 198000, 'b2c3d4e5f6a10829', 13.2489000, 77.7123000, 'duplicate_detected');

-- ----------------------------------------------------------------------------
-- 9. RISK SIGNALS (Synthetic Evidence & Signals)
-- ----------------------------------------------------------------------------
INSERT INTO risk_signals (id, case_id, category, signal_name, severity, confidence_score, evidence_payload, description) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '55555555-5555-5555-5555-555555555503', 'price', 'BENCHMARK_PRICE_DEVIATION_HIGH', 'high', 94.50, '{"claimed_unit_price": 115000, "benchmark_avg": 52000, "variance_pct": 121.15, "category": "Solar Inverter"}'::jsonb, 'Invoiced price exceeds category benchmark upper band by +121.15%. Requires price justification review.'),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '55555555-5555-5555-5555-555555555505', 'serial_asset', 'DUPLICATE_SERIAL_CROSS_CASE_DETECTED', 'critical', 99.80, '{"serial_number": "ASP-2025-99881", "prior_case_id": "55555555-5555-5555-5555-555555555501", "prior_case_number": "CAS-2026-001"}'::jsonb, 'Serial number ASP-2025-99881 is already registered to active verified Case CAS-2026-001 in Pune.'),
('cccccccc-cccc-cccc-cccc-cccccccccccc', '55555555-5555-5555-5555-555555555507', 'dealer_network', 'SHARED_ADDRESS_DEALER_CUSTOMER', 'high', 92.00, '{"dealer_address": "88, Agro Yard Extension, Hebbal, Bengaluru", "customer_address": "88, Agro Yard Extension, Hebbal, Bengaluru"}'::jsonb, 'Borrower claimed installation location matches dealer registered place of business.'),
('dddddddd-dddd-dddd-dddd-dddddddddddd', '55555555-5555-5555-5555-555555555510', 'geo', 'GEOLOCATION_DISCREPANCY_EXIF_VS_CLAIMED', 'medium', 78.20, '{"claimed_coordinates": [18.1530, 74.5775], "exif_coordinates": [18.8256, 74.3789], "distance_km": 74.2}'::jsonb, 'Distance between claimed site and image capture coordinates exceeds 70 km threshold.');

-- ----------------------------------------------------------------------------
-- 10. RISK SCORES
-- ----------------------------------------------------------------------------
INSERT INTO risk_scores (id, case_id, overall_score, risk_level, price_anomaly_score, image_anomaly_score, dealer_network_score, serial_anomaly_score, summary_reasoning) VALUES
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1', '55555555-5555-5555-5555-555555555501', 8, 'low', 5, 0, 8, 0, 'Clean case. Asset serial, invoice benchmark pricing, and image metadata fully consistent.'),
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee2', '55555555-5555-5555-5555-555555555502', 12, 'low', 8, 4, 10, 0, 'Low risk. Pricing aligned with market rate; telemetry verified within tolerance.'),
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee3', '55555555-5555-5555-5555-555555555503', 74, 'high', 88, 10, 35, 0, 'High risk identified due to +121% invoice price variance against market benchmark for 5kVA Inverter.'),
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee4', '55555555-5555-5555-5555-555555555505', 96, 'critical', 15, 85, 40, 99, 'Critical anomaly: Exact duplicate serial number match against active operational installation CAS-2026-001.'),
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee5', '55555555-5555-5555-5555-555555555507', 82, 'high', 10, 20, 95, 10, 'High risk: Entity relationship anomaly detected between dealer place of business and customer installation site.');

-- ----------------------------------------------------------------------------
-- 11. ENTITY RELATIONSHIPS
-- ----------------------------------------------------------------------------
INSERT INTO entity_relationships (id, case_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type, risk_weight, metadata) VALUES
('ffffffff-ffff-ffff-ffff-fffffffffff1', '55555555-5555-5555-5555-555555555507', 'dealer', '22222222-2222-2222-2222-222222222203', 'address', '88_agro_yard_hebbal_560024', 'registered_office_match', 85.00, '{"details": "Direct address match between dealer and loan applicant"}'::jsonb),
('ffffffff-ffff-ffff-ffff-fffffffffff2', '55555555-5555-5555-5555-555555555508', 'dealer', '22222222-2222-2222-2222-222222222203', 'phone', '+91-9823000003', 'contact_cluster_overlap', 70.00, '{"details": "Customer phone contact cluster overlaps with dealer director record"}'::jsonb);

-- ----------------------------------------------------------------------------
-- 12. VERIFICATION TASKS
-- ----------------------------------------------------------------------------
INSERT INTO verification_tasks (id, case_id, task_type, status, assigned_to, instructions, findings) VALUES
('12121212-1212-1212-1212-121212121201', '55555555-5555-5555-5555-555555555503', 'document_reupload', 'pending', 'risk.officer1@diavn.synthetic', 'Request dealer itemized rate card and manufacturer price memo for SG-5KVA-HYBRID.', NULL),
('12121212-1212-1212-1212-121212121202', '55555555-5555-5555-5555-555555555505', 'oem_serial_check', 'in_progress', 'lead.auditor@diavn.synthetic', 'Contact AquaSun OEM dispatch desk to verify batch shipping destination for serial ASP-2025-99881.', 'Initial inquiry sent to OEM registry.'),
('12121212-1212-1212-1212-121212121203', '55555555-5555-5555-5555-555555555510', 'physical_site_visit', 'pending', 'field.verifier@diavn.synthetic', 'Conduct geo-verified physical inspection at Baramati farm coordinates to verify physical pump installation.', NULL);

-- ----------------------------------------------------------------------------
-- 13. AUDIT LOG
-- ----------------------------------------------------------------------------
INSERT INTO audit_log (id, actor_id, action, entity_type, entity_id, payload) VALUES
('13131313-1313-1313-1313-131313131301', '11111111-1111-1111-1111-111111111101', 'CASE_INITIALIZED', 'case', '55555555-5555-5555-5555-555555555501', '{"seed_operation": true, "environment": "synthetic_seed"}'::jsonb),
('13131313-1313-1313-1313-131313131302', '11111111-1111-1111-1111-111111111102', 'ANOMALY_FLAGGED', 'case', '55555555-5555-5555-5555-555555555505', '{"reason": "DUPLICATE_SERIAL_CROSS_CASE_DETECTED"}'::jsonb);
