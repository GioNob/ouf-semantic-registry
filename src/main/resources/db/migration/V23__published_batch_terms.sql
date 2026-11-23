-- norm-v1, PostgreSQL 17 / UTF8. Full default folds (Unicode 15.1, C and F)
-- differ from locale-specific lower(). The runtime conformance test compares
-- this complete mapping with ICU4J 75.1, including unchanged scalars.
CREATE TABLE ouf_sem.norm_v1_fold (
    codepoint integer PRIMARY KEY,
    folded text NOT NULL
);
INSERT INTO ouf_sem.norm_v1_fold
SELECT cp, chr(cp + delta)
FROM (VALUES
    (65,90,1,32), (181,181,1,775), (192,214,1,32), (216,222,1,32),
    (256,302,2,1), (306,310,2,1), (313,327,2,1), (330,374,2,1),
    (376,376,1,-121), (377,381,2,1), (383,383,1,-268), (385,385,1,210),
    (386,388,2,1), (390,390,1,206), (391,391,1,1), (393,394,1,205),
    (395,395,1,1), (398,398,1,79), (399,399,1,202), (400,400,1,203),
    (401,401,1,1), (403,403,1,205), (404,404,1,207), (406,406,1,211),
    (407,407,1,209), (408,408,1,1), (412,412,1,211), (413,413,1,213),
    (415,415,1,214), (416,420,2,1), (422,422,1,218), (423,423,1,1),
    (425,425,1,218), (428,428,1,1), (430,430,1,218), (431,431,1,1),
    (433,434,1,217), (435,437,2,1), (439,439,1,219), (440,444,4,1),
    (452,452,1,2), (453,453,1,1), (455,455,1,2), (456,456,1,1),
    (458,458,1,2), (459,475,2,1), (478,494,2,1), (497,497,1,2),
    (498,500,2,1), (502,502,1,-97), (503,503,1,-56), (504,542,2,1),
    (544,544,1,-130), (546,562,2,1), (570,570,1,10795), (571,571,1,1),
    (573,573,1,-163), (574,574,1,10792), (577,577,1,1), (579,579,1,-195),
    (580,580,1,69), (581,581,1,71), (582,590,2,1), (837,837,1,116),
    (880,882,2,1), (886,886,1,1), (895,895,1,116), (902,902,1,38),
    (904,906,1,37), (908,908,1,64), (910,911,1,63), (913,929,1,32),
    (931,939,1,32), (962,962,1,1), (975,975,1,8), (976,976,1,-30),
    (977,977,1,-25), (981,981,1,-15), (982,982,1,-22), (984,1006,2,1),
    (1008,1008,1,-54), (1009,1009,1,-48), (1012,1012,1,-60), (1013,1013,1,-64),
    (1015,1015,1,1), (1017,1017,1,-7), (1018,1018,1,1), (1021,1023,1,-130),
    (1024,1039,1,80), (1040,1071,1,32), (1120,1152,2,1), (1162,1214,2,1),
    (1216,1216,1,15), (1217,1229,2,1), (1232,1326,2,1), (1329,1366,1,48),
    (4256,4293,1,7264), (4295,4301,6,7264), (5112,5117,1,-8), (7296,7296,1,-6222),
    (7297,7297,1,-6221), (7298,7298,1,-6212), (7299,7300,1,-6210), (7301,7301,1,-6211),
    (7302,7302,1,-6204), (7303,7303,1,-6180), (7304,7304,1,35267), (7312,7354,1,-3008),
    (7357,7359,1,-3008), (7680,7828,2,1), (7835,7835,1,-58), (7840,7934,2,1),
    (7944,7951,1,-8), (7960,7965,1,-8), (7976,7983,1,-8), (7992,7999,1,-8),
    (8008,8013,1,-8), (8025,8031,2,-8), (8040,8047,1,-8), (8120,8121,1,-8),
    (8122,8123,1,-74), (8126,8126,1,-7173), (8136,8139,1,-86), (8152,8153,1,-8),
    (8154,8155,1,-100), (8168,8169,1,-8), (8170,8171,1,-112), (8172,8172,1,-7),
    (8184,8185,1,-128), (8186,8187,1,-126), (8486,8486,1,-7517), (8490,8490,1,-8383),
    (8491,8491,1,-8262), (8498,8498,1,28), (8544,8559,1,16), (8579,8579,1,1),
    (9398,9423,1,26), (11264,11311,1,48), (11360,11360,1,1), (11362,11362,1,-10743),
    (11363,11363,1,-3814), (11364,11364,1,-10727), (11367,11371,2,1), (11373,11373,1,-10780),
    (11374,11374,1,-10749), (11375,11375,1,-10783), (11376,11376,1,-10782), (11378,11381,3,1),
    (11390,11391,1,-10815), (11392,11490,2,1), (11499,11501,2,1), (11506,42560,31054,1),
    (42562,42604,2,1), (42624,42650,2,1), (42786,42798,2,1), (42802,42862,2,1),
    (42873,42875,2,1), (42877,42877,1,-35332), (42878,42886,2,1), (42891,42891,1,1),
    (42893,42893,1,-42280), (42896,42898,2,1), (42902,42920,2,1), (42922,42922,1,-42308),
    (42923,42923,1,-42319), (42924,42924,1,-42315), (42925,42925,1,-42305), (42926,42926,1,-42308),
    (42928,42928,1,-42258), (42929,42929,1,-42282), (42930,42930,1,-42261), (42931,42931,1,928),
    (42932,42946,2,1), (42948,42948,1,-48), (42949,42949,1,-42307), (42950,42950,1,-35384),
    (42951,42953,2,1), (42960,42966,6,1), (42968,42997,29,1), (43888,43967,1,-38864),
    (65313,65338,1,32), (66560,66599,1,40), (66736,66771,1,40), (66928,66938,1,39),
    (66940,66954,1,39), (66956,66962,1,39), (66964,66965,1,39), (68736,68786,1,64),
    (71840,71871,1,32), (93760,93791,1,32), (125184,125217,1,34)
) AS mapping(first_cp, last_cp, stride, delta)
CROSS JOIN LATERAL generate_series(first_cp, last_cp, stride) cp;

INSERT INTO ouf_sem.norm_v1_fold VALUES
    (223,U&'\0073\0073'), (304,U&'\0069\0307'), (329,U&'\02bc\006e'), (496,U&'\006a\030c'),
    (912,U&'\03b9\0308\0301'), (944,U&'\03c5\0308\0301'), (1415,U&'\0565\0582'), (7830,U&'\0068\0331'),
    (7831,U&'\0074\0308'), (7832,U&'\0077\030a'), (7833,U&'\0079\030a'), (7834,U&'\0061\02be'),
    (7838,U&'\0073\0073'), (8016,U&'\03c5\0313'), (8018,U&'\03c5\0313\0300'), (8020,U&'\03c5\0313\0301'),
    (8022,U&'\03c5\0313\0342'), (8064,U&'\1f00\03b9'), (8065,U&'\1f01\03b9'), (8066,U&'\1f02\03b9'),
    (8067,U&'\1f03\03b9'), (8068,U&'\1f04\03b9'), (8069,U&'\1f05\03b9'), (8070,U&'\1f06\03b9'),
    (8071,U&'\1f07\03b9'), (8072,U&'\1f00\03b9'), (8073,U&'\1f01\03b9'), (8074,U&'\1f02\03b9'),
    (8075,U&'\1f03\03b9'), (8076,U&'\1f04\03b9'), (8077,U&'\1f05\03b9'), (8078,U&'\1f06\03b9'),
    (8079,U&'\1f07\03b9'), (8080,U&'\1f20\03b9'), (8081,U&'\1f21\03b9'), (8082,U&'\1f22\03b9'),
    (8083,U&'\1f23\03b9'), (8084,U&'\1f24\03b9'), (8085,U&'\1f25\03b9'), (8086,U&'\1f26\03b9'),
    (8087,U&'\1f27\03b9'), (8088,U&'\1f20\03b9'), (8089,U&'\1f21\03b9'), (8090,U&'\1f22\03b9'),
    (8091,U&'\1f23\03b9'), (8092,U&'\1f24\03b9'), (8093,U&'\1f25\03b9'), (8094,U&'\1f26\03b9'),
    (8095,U&'\1f27\03b9'), (8096,U&'\1f60\03b9'), (8097,U&'\1f61\03b9'), (8098,U&'\1f62\03b9'),
    (8099,U&'\1f63\03b9'), (8100,U&'\1f64\03b9'), (8101,U&'\1f65\03b9'), (8102,U&'\1f66\03b9'),
    (8103,U&'\1f67\03b9'), (8104,U&'\1f60\03b9'), (8105,U&'\1f61\03b9'), (8106,U&'\1f62\03b9'),
    (8107,U&'\1f63\03b9'), (8108,U&'\1f64\03b9'), (8109,U&'\1f65\03b9'), (8110,U&'\1f66\03b9'),
    (8111,U&'\1f67\03b9'), (8114,U&'\1f70\03b9'), (8115,U&'\03b1\03b9'), (8116,U&'\03ac\03b9'),
    (8118,U&'\03b1\0342'), (8119,U&'\03b1\0342\03b9'), (8124,U&'\03b1\03b9'), (8130,U&'\1f74\03b9'),
    (8131,U&'\03b7\03b9'), (8132,U&'\03ae\03b9'), (8134,U&'\03b7\0342'), (8135,U&'\03b7\0342\03b9'),
    (8140,U&'\03b7\03b9'), (8146,U&'\03b9\0308\0300'), (8147,U&'\03b9\0308\0301'), (8150,U&'\03b9\0342'),
    (8151,U&'\03b9\0308\0342'), (8162,U&'\03c5\0308\0300'), (8163,U&'\03c5\0308\0301'), (8164,U&'\03c1\0313'),
    (8166,U&'\03c5\0342'), (8167,U&'\03c5\0308\0342'), (8178,U&'\1f7c\03b9'), (8179,U&'\03c9\03b9'),
    (8180,U&'\03ce\03b9'), (8182,U&'\03c9\0342'), (8183,U&'\03c9\0342\03b9'), (8188,U&'\03c9\03b9'),
    (64256,U&'\0066\0066'), (64257,U&'\0066\0069'), (64258,U&'\0066\006c'), (64259,U&'\0066\0066\0069'),
    (64260,U&'\0066\0066\006c'), (64261,U&'\0073\0074'), (64262,U&'\0073\0074'), (64275,U&'\0574\0576'),
    (64276,U&'\0574\0565'), (64277,U&'\0574\056b'), (64278,U&'\057e\0576'), (64279,U&'\0574\056d');

CREATE FUNCTION ouf_sem.norm_v1(input text) RETURNS text
LANGUAGE sql STABLE STRICT PARALLEL SAFE AS $$
    SELECT btrim(regexp_replace(normalize(
        CASE WHEN octet_length(input) = char_length(input)
             THEN translate(input, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')
             ELSE (SELECT coalesce(string_agg(coalesce(f.folded, c.ch), '' ORDER BY c.pos), '')
                   FROM string_to_table(normalize(input, NFC), NULL) WITH ORDINALITY c(ch,pos)
                   LEFT JOIN ouf_sem.norm_v1_fold f ON f.codepoint = ascii(c.ch))
        END, NFC) COLLATE "C",
        U&'[\0009-\000D\0020\0085\00A0\1680\2000-\200A\2028\2029\202F\205F\3000]+', ' ', 'g'))
$$;

CREATE TABLE ouf_sem.revision_batch_term (
    revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE CASCADE,
    artifact_type varchar(32) NOT NULL,
    language text COLLATE "C" NOT NULL,
    kind text COLLATE "C" NOT NULL CHECK (kind IN ('LABEL','LOCAL')),
    term bytea NOT NULL,
    PRIMARY KEY (revision_id, language, kind, term)
);

CREATE FUNCTION ouf_sem.batch_terms(labels jsonb, local_name text)
RETURNS TABLE(language text, kind text, term bytea) LANGUAGE sql STABLE AS $$
    WITH normalized AS MATERIALIZED (
        SELECT lower(e.key COLLATE "C") AS lang, ouf_sem.norm_v1(e.value #>> '{}') AS label
        FROM jsonb_each(CASE WHEN jsonb_typeof(labels) = 'object' THEN labels ELSE '{}'::jsonb END) e
        WHERE e.key COLLATE "C" ~ '^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8}){0,3}$'
          AND jsonb_typeof(e.value) = 'string'
    ), terms AS (
        -- Keep one scalar beyond the 256-scalar intent limit to distinguish
        -- exact labels from longer prefixes, within PostgreSQL's btree key limit.
        SELECT lang, 'LABEL' AS kind, left(label,257) AS value FROM normalized WHERE label <> ''
        UNION
        SELECT lang, 'LOCAL', ouf_sem.norm_v1(local_name) FROM normalized WHERE label <> ''
    )
    SELECT lang, terms.kind, convert_to(value,'UTF8') FROM terms
    WHERE terms.kind = 'LABEL' OR char_length(value) BETWEEN 1 AND 256
$$;

CREATE FUNCTION ouf_sem.refresh_batch_terms(rev uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    labels jsonb;
    name text;
    typ text;
BEGIN
    SELECT r.label_json, a.local_name, a.artifact_type INTO STRICT labels, name, typ
    FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING (artifact_id)
    WHERE r.revision_id = rev FOR SHARE OF a,r;
    DELETE FROM ouf_sem.revision_batch_term WHERE revision_id = rev;
    IF typ IN ('CLASS','PROPERTY','DATATYPE') THEN
        INSERT INTO ouf_sem.revision_batch_term
        SELECT rev, typ, t.* FROM ouf_sem.batch_terms(labels,name) t;
    END IF;
END
$$;

CREATE FUNCTION ouf_sem.index_revision_batch_terms() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM ouf_sem.refresh_batch_terms(NEW.revision_id);
    RETURN NEW;
END
$$;
CREATE TRIGGER revision_batch_terms AFTER INSERT OR UPDATE OF label_json,artifact_id
ON ouf_sem.artifact_revision FOR EACH ROW EXECUTE FUNCTION ouf_sem.index_revision_batch_terms();

CREATE FUNCTION ouf_sem.index_artifact_batch_terms() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM ouf_sem.refresh_batch_terms(r.revision_id)
    FROM ouf_sem.artifact_revision r WHERE r.artifact_id = NEW.artifact_id ORDER BY r.revision_id;
    RETURN NEW;
END
$$;
CREATE TRIGGER artifact_batch_terms AFTER UPDATE OF local_name,artifact_type
ON ouf_sem.semantic_artifact FOR EACH ROW
WHEN (OLD.local_name IS DISTINCT FROM NEW.local_name OR OLD.artifact_type IS DISTINCT FROM NEW.artifact_type)
EXECUTE FUNCTION ouf_sem.index_artifact_batch_terms();

-- Same projection as both writer triggers. Safe to replay with the index populated.
CREATE PROCEDURE ouf_sem.backfill_batch_terms() LANGUAGE sql AS $$
    LOCK TABLE ouf_sem.semantic_artifact, ouf_sem.artifact_revision IN SHARE MODE;
    INSERT INTO ouf_sem.revision_batch_term
    SELECT r.revision_id, a.artifact_type, t.*
    FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING (artifact_id)
    CROSS JOIN LATERAL ouf_sem.batch_terms(r.label_json,a.local_name) t
    WHERE a.artifact_type IN ('CLASS','PROPERTY','DATATYPE')
    ON CONFLICT DO NOTHING;
$$;
CALL ouf_sem.backfill_batch_terms();

CREATE INDEX revision_batch_term_lookup ON ouf_sem.revision_batch_term
    (artifact_type,language,kind,term) INCLUDE (revision_id);
CREATE INDEX publication_member_by_revision ON ouf_sem.semantic_publication_member
    (revision_id) INCLUDE (publication_set_id);
ANALYZE ouf_sem.revision_batch_term;
