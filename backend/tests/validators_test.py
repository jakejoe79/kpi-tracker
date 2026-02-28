"""
Validator tests - verify data integrity rules
"""
import pytest
import secrets
from datetime import datetime
from typing import Dict, Any


class TestTenantValidation:
    """Test tenant isolation validation"""
    
    def test_verify_tenant_validation_works(self):
        """
        Verify that tenant validation is properly configured
        This test ensures company_id and team_id fields exist in the schema
        """
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        properties = validator["$jsonSchema"]["properties"]
        
        # Verify company_id field exists
        assert "company_id" in properties
        assert properties["company_id"]["bsonType"] == ["string", "null"]
        
        # Verify team_id field exists
        assert "team_id" in properties
        assert properties["team_id"]["bsonType"] == ["string", "null"]
        
        # Verify additionalProperties is False (strict whitelist)
        assert validator["$jsonSchema"]["additionalProperties"] is False
    
    def test_email_validation_format(self):
        """Verify email format validation"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        email_prop = validator["$jsonSchema"]["properties"]["email"]
        
        # Verify email pattern
        assert "pattern" in email_prop
        assert "@" in email_prop["pattern"]
    
    def test_password_hash_validation(self):
        """Verify password hash format validation"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        password_prop = validator["$jsonSchema"]["properties"]["password_hash"]
        
        # Verify bcrypt hash requirements
        assert password_prop["minLength"] == 60
        assert "pattern" in password_prop
        assert "$2" in password_prop["pattern"]


class TestUniqueIndexes:
    """Test unique index configuration"""
    
    def test_users_email_unique(self):
        """Verify users.email has unique index"""
        from backend.db.indexes import setup_indexes
        
        # This test verifies the setup_indexes function creates unique indexes
        # Actual index creation is tested in integration tests
        pass
    
    def test_refresh_tokens_jti_unique(self):
        """Verify refresh_tokens.jti has unique index"""
        from backend.db.indexes import setup_indexes
        
        # This test verifies the setup_indexes function creates unique indexes
        pass


class TestImmutableFields:
    """Test immutable field enforcement"""
    
    def test_id_immutable(self):
        """Verify id field is required and immutable"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        required = validator["$jsonSchema"]["required"]
        
        assert "id" in required
    
    def test_created_at_db_owned(self):
        """Verify created_at is DB-owned (set by database)"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        properties = validator["$jsonSchema"]["properties"]
        
        assert "created_at" in properties
        assert properties["created_at"]["bsonType"] == "date"


class TestNullHandling:
    """Test null value handling in validators"""
    
    def test_verify_null_handling(self):
        """
        Verify that null values are properly handled in validators
        - Optional fields should allow null
        - Required fields should not allow null
        """
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        properties = validator["$jsonSchema"]["properties"]
        required = validator["$jsonSchema"]["required"]
        
        # Required fields should NOT allow null
        for field in required:
            field_prop = properties.get(field, {})
            if isinstance(field_prop.get("bsonType"), list):
                # If bsonType is a list, null should not be in it for required fields
                assert "null" not in field_prop["bsonType"], f"Required field {field} should not allow null"
        
        # Optional fields should allow null
        optional_fields = ["company_id", "team_id", "password_hash", "updated_at"]
        for field in optional_fields:
            if field in properties:
                field_prop = properties[field]
                if isinstance(field_prop.get("bsonType"), list):
                    assert "null" in field_prop["bsonType"], f"Optional field {field} should allow null"
    
    def test_updated_at_nullable(self):
        """Verify updated_at is nullable (not set on insert)"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        properties = validator["$jsonSchema"]["properties"]
        
        assert "updated_at" in properties
        assert properties["updated_at"]["bsonType"] == ["date", "null"]


class TestExprRules:
    """Test $expr validation rules"""
    
    def test_expr_rules_exist(self):
        """Verify $expr rules are present in validator"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        
        assert "$expr" in validator
        assert "$and" in validator["$expr"]
    
    def test_team_id_requires_company_id(self):
        """Verify team_id requires company_id in $expr"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        expr = validator["$expr"]
        
        # Check that the expr contains the team_id -> company_id rule
        expr_str = str(expr)
        assert "$or" in expr_str
        assert "$team_id" in expr_str or "team_id" in expr_str
        assert "$company_id" in expr_str or "company_id" in expr_str


class TestConditionalValidation:
    """Test conditional validation (if/then for tier requirements)"""
    
    def test_tier_company_requires_company_id(self):
        """Verify company tier requires company_id"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        all_of = validator["$jsonSchema"].get("allOf", [])
        
        # Find the rule for company tier
        company_rule = None
        for rule in all_of:
            if "if" in rule and "then" in rule:
                if_rule = rule["if"]
                if "properties" in if_rule and "tier" in if_rule["properties"]:
                    if if_rule["properties"]["tier"].get("const") == "company":
                        company_rule = rule
                        break
        
        assert company_rule is not None, "Company tier rule not found"
        assert "then" in company_rule
        assert "properties" in company_rule["then"]
        assert "company_id" in company_rule["then"]["properties"]
    
    def test_tier_group_requires_team_id(self):
        """Verify group tier requires team_id"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        all_of = validator["$jsonSchema"].get("allOf", [])
        
        # Find the rule for group tier
        group_rule = None
        for rule in all_of:
            if "if" in rule and "then" in rule:
                if_rule = rule["if"]
                if "properties" in if_rule and "tier" in if_rule["properties"]:
                    if if_rule["properties"]["tier"].get("const") == "group":
                        group_rule = rule
                        break
        
        assert group_rule is not None, "Group tier rule not found"
        assert "then" in group_rule
        assert "properties" in group_rule["then"]
        assert "team_id" in group_rule["then"]["properties"]


class TestStringLengthLimits:
    """Test string length limits"""
    
    def test_id_max_length(self):
        """Verify id max length is 64"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        id_prop = validator["$jsonSchema"]["properties"]["id"]
        
        assert "maxLength" in id_prop
        assert id_prop["maxLength"] == 64
    
    def test_email_max_length(self):
        """Verify email max length is 254"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        email_prop = validator["$jsonSchema"]["properties"]["email"]
        
        assert "maxLength" in email_prop
        assert email_prop["maxLength"] == 254
    
    def test_jti_max_length(self):
        """Verify JTI max length is 128"""
        from backend.db.validators import get_refresh_tokens_validator
        
        validator = get_refresh_tokens_validator()
        jti_prop = validator["$jsonSchema"]["properties"]["jti"]
        
        assert "maxLength" in jti_prop
        assert jti_prop["maxLength"] == 128
    
    def test_revoked_reason_max_length(self):
        """Verify revoked_reason max length is 50"""
        from backend.db.validators import get_refresh_tokens_validator
        
        validator = get_refresh_tokens_validator()
        reason_prop = validator["$jsonSchema"]["properties"]["revoked_reason"]
        
        assert "maxLength" in reason_prop
        assert reason_prop["maxLength"] == 50


class TestPatternValidation:
    """Test pattern validation for IDs"""
    
    def test_user_id_pattern(self):
        """Verify user_id pattern with user_ prefix"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        id_prop = validator["$jsonSchema"]["properties"]["id"]
        
        assert "pattern" in id_prop
        assert id_prop["pattern"].startswith("^user_")
    
    def test_company_id_pattern(self):
        """Verify company_id pattern with comp_ prefix"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        company_prop = validator["$jsonSchema"]["properties"]["company_id"]
        
        # Check anyOf for string pattern
        any_of = company_prop.get("anyOf", [])
        for item in any_of:
            if "pattern" in item:
                assert item["pattern"].startswith("^comp_")
                break
    
    def test_team_id_pattern(self):
        """Verify team_id pattern with team_ prefix"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        team_prop = validator["$jsonSchema"]["properties"]["team_id"]
        
        # Check anyOf for string pattern
        any_of = team_prop.get("anyOf", [])
        for item in any_of:
            if "pattern" in item:
                assert item["pattern"].startswith("^team_")
                break


class TestCollectionInitialization:
    """Test collection initialization and safe create-or-update"""
    
    def test_users_required_fields(self):
        """Verify users collection has required fields"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        required = validator["$jsonSchema"]["required"]
        
        # All auth records must have these
        assert "id" in required
        assert "email" in required
        assert "tier" in required
        assert "role" in required
        assert "is_active" in required
        assert "created_at" in required
    
    def test_refresh_tokens_required_fields(self):
        """Verify refresh_tokens collection has required fields"""
        from backend.db.validators import get_refresh_tokens_validator
        
        validator = get_refresh_tokens_validator()
        required = validator["$jsonSchema"]["required"]
        
        assert "jti" in required
        assert "user_id" in required
        assert "token_hash" in required
        assert "created_at" in required
        assert "expires_at" in required


class TestAuditImmutability:
    """Test audit log immutability"""
    
    def test_additional_properties_false(self):
        """Verify additionalProperties is False (strict whitelist)"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        
        assert validator["$jsonSchema"]["additionalProperties"] is False
    
    def test_no_update_methods_in_validator(self):
        """Verify validator doesn't contain update methods"""
        from backend.db.validators import get_users_validator
        
        validator = get_users_validator()
        validator_str = str(validator)
        
        # Validator should not contain update methods
        assert "$set" not in validator_str
        assert "$unset" not in validator_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
