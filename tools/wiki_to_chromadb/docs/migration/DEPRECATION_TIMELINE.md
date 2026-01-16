# Deprecation Timeline

## Version History

### Version 2.0.0 (Current) - January 14, 2026

**Status**: Deprecation warnings added

**Changes**:
- ✅ Refactored pipeline with Pydantic models
- ✅ Centralized configuration (`PipelineConfig`)
- ✅ Structured logging (`PipelineLogger`)
- ✅ Type-safe data models (`WikiPage`, `Chunk`, etc.)
- ✅ 62/66 tests passing (94% coverage)
- ⚠️ Deprecated modules show warnings on import
- 📄 Migration guide published

**Deprecated Modules**:
- `chunker.py` → Use `chunker_v2.py` (removal: March 2026)
- ~~`metadata_enrichment_old.py`~~ → ✅ **Deleted January 14, 2026**
- ~~`process_wiki_old.py`~~ → ✅ **Deleted January 14, 2026**

**Action Required**:
- Review [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- Start migration to new modules
- Test with new pipeline

---

### Version 2.1.0 (Planned) - February 2026

**Status**: Migration support period

**Planned Features**:
- Migration assistance tooling
- Additional test coverage
- Performance optimizations
- Documentation improvements

**Action Items**:
- Complete migration from deprecated modules
- Report any migration issues
- Test thoroughly in staging environment

**Support**:
- Migration questions answered
- Bug fixes for new pipeline
- Rollback support if critical issues found

---

### Version 3.0.0 (Planned) - March 2026

**Status**: Breaking changes - deprecated modules removed

**Breaking Changes**:
- ❌ **REMOVES** `chunker.py`
- ❌ **REMOVES** `metadata_enrichment_old.py`
- ❌ **REMOVES** `process_wiki_old.py`
- ❌ Import errors for deprecated modules

**Required**:
- ✅ Must complete migration before this release
- ✅ Must use new modules (`chunker_v2`, `metadata_enrichment`, `process_wiki`)
- ✅ Must update all imports

**New Features**:
- Additional Pydantic validators
- Enhanced error messages
- Performance improvements
- Extended test coverage

---

## Migration Deadlines

| Deadline | Milestone | Action |
|----------|-----------|--------|
| **January 14, 2026** | Deprecation warnings added | Start migration planning |
| **January 31, 2026** | End of month 1 | Begin code migration |
| **February 14, 2026** | Mid-migration checkpoint | Complete 50% of migration |
| **February 28, 2026** | Migration deadline | Complete 100% of migration |
| **March 1, 2026** | Version 3.0.0 release | Deprecated modules removed |

---

## What Happens If You Don't Migrate?

### Immediate (Version 2.0.0 - Now)
- ⚠️ **Warnings** on every import of `chunker.py`
- ⚠️ Terminal/log output shows deprecation messages
- ✅ Code still works (backward compatible)
- ❌ **Backup files deleted** (`*_old.py` removed January 14, 2026)

### February 2026 (Version 2.1.0)
- ⚠️ **Louder warnings** (may be promoted to errors in tests)
- ⚠️ CI/CD pipelines may fail on warnings
- ✅ Code still works (last backward-compatible release)

### March 2026 (Version 3.0.0)
- ❌ **ImportError** when trying to import deprecated modules
- ❌ **Code breaks** - deprecated files deleted
- ❌ **No rollback** - must use new modules
- ❌ **Production failures** if not migrated

---

## How to Check If You're Affected

### 1. Search Your Codebase

```bash
# Search for deprecated imports
grep -r "from chunker import" .

# Windows PowerShell
Get-ChildItem -Recurse -Filter "*.py" | Select-String "from chunker import"

# Note: Backup files (*_old.py) were deleted January 14, 2026
```

### 2. Run Your Code

If you see warnings like:
```
DeprecationWarning: chunker.py is deprecated and will be removed in version 3.0.0 (March 2026).
Use chunker_v2.py instead for type-safe chunking with Pydantic models.
```

**You need to migrate.**

### 3. Check Import Statements

If your code has:
```python
from chunker import SemanticChunker  # ❌ Deprecated (March 2026 removal)
```

**You need to migrate.**

Note: `*_old.py` backup files were already deleted (January 14, 2026).

---

## Migration Resources

### Documentation
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Complete migration instructions
- **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Architecture overview
- **[INTEGRATION_TESTS.md](INTEGRATION_TESTS.md)** - Test coverage details

### Code Examples
- **[tests/unit/](tests/unit/)** - Unit test examples using new modules
- **[tests/integration/](tests/integration/)** - Integration test examples
- **[example_julie_knowledge.py](example_julie_knowledge.py)** - Full usage example

### Testing
```bash
# Run all tests to verify migration
python -m pytest tests/ -v

# Run specific migration tests
python -m pytest tests/unit/test_chunker_v2.py -v
python -m pytest tests/unit/test_metadata_enrichment.py -v
python -m pytest tests/integration/test_full_pipeline.py -v
```

---

## Support Policy

### Version 2.x (Current - February 2026)
- ✅ **Full support** for both old and new modules
- ✅ Bug fixes for deprecated modules
- ✅ Migration assistance
- ✅ Rollback support if issues arise

### Version 3.x (March 2026+)
- ✅ **Support only** for new modules
- ❌ **No support** for deprecated modules (deleted)
- ❌ **No rollback** to deprecated modules
- ✅ Bug fixes for new pipeline only

---

## FAQ

**Q: Can I continue using the old modules after March 2026?**  
A: No. They will be deleted from the codebase in version 3.0.0.

**Q: What if I find a bug in the new modules?**  
A: Report it immediately. We'll fix it or provide guidance. Rollback to `*_old.py` is available until March 2026.

**Q: Can the deadline be extended?**  
A: Unlikely. Two months is sufficient for migration. Start early to avoid last-minute issues.

**Q: Will my existing ChromaDB data still work?**  
A: Yes. The database format is unchanged. Only the code that creates/queries it is refactored.

**Q: Do I need to re-process the wiki?**  
A: No, unless you want to take advantage of new metadata features. Existing data is compatible.

**Q: What if I have custom code using deprecated modules?**  
A: Follow the [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) to update your custom code. The patterns are the same.

---

## Contact

Questions or issues? Check:
1. [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Common issues and solutions
2. Code documentation - Inline comments and docstrings
3. Test files - Examples of correct usage

---

**Last Updated**: January 14, 2026  
**Current Version**: 2.0.0  
**Next Version**: 3.0.0 (March 2026)
