"""Stack profiles (live-test stand-in): prints candidate facts."""
print("candidate sqlite3: stdlib, transactional, single file, concurrent readers")
print("candidate json: stdlib, whole-file rewrite, no concurrency control")
print("candidate shelve: stdlib, dbm-backed, platform-dependent file format")
