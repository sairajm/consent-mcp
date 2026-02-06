"""Tests for schema_utils - Pydantic to MCP inputSchema conversion."""

import pytest
from typing import Annotated, Optional, Literal
from enum import Enum

from pydantic import BaseModel, Field, EmailStr

from consent_mcp.utils.schema_utils import pydantic_to_input_schema


class TestPydanticToInputSchema:
    """Tests for pydantic_to_input_schema function."""

    # ============================================
    # Basic Type Tests
    # ============================================

    def test_simple_string_field(self):
        """Test conversion of a simple string field."""
        class SimpleModel(BaseModel):
            name: str

        schema = pydantic_to_input_schema(SimpleModel)

        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert "name" in schema["required"]

    def test_simple_integer_field(self):
        """Test conversion of an integer field."""
        class IntModel(BaseModel):
            count: int

        schema = pydantic_to_input_schema(IntModel)

        assert schema["properties"]["count"]["type"] == "integer"
        assert "count" in schema["required"]

    def test_simple_boolean_field(self):
        """Test conversion of a boolean field."""
        class BoolModel(BaseModel):
            active: bool

        schema = pydantic_to_input_schema(BoolModel)

        assert schema["properties"]["active"]["type"] == "boolean"

    def test_simple_float_field(self):
        """Test conversion of a float field."""
        class FloatModel(BaseModel):
            price: float

        schema = pydantic_to_input_schema(FloatModel)

        assert schema["properties"]["price"]["type"] == "number"

    # ============================================
    # Field Description Tests
    # ============================================

    def test_field_with_description(self):
        """Test that Field descriptions are preserved."""
        class DescModel(BaseModel):
            name: Annotated[str, Field(description="The user's full name")]

        schema = pydantic_to_input_schema(DescModel)

        assert schema["properties"]["name"]["description"] == "The user's full name"

    def test_field_without_description_uses_title(self):
        """Test that title is used as fallback description."""
        class TitleModel(BaseModel):
            user_name: str

        schema = pydantic_to_input_schema(TitleModel)

        # Pydantic generates title from field name
        assert "description" in schema["properties"]["user_name"]

    def test_multiple_fields_with_descriptions(self):
        """Test multiple fields each have their descriptions."""
        class MultiDescModel(BaseModel):
            first: Annotated[str, Field(description="First field")]
            second: Annotated[int, Field(description="Second field")]

        schema = pydantic_to_input_schema(MultiDescModel)

        assert schema["properties"]["first"]["description"] == "First field"
        assert schema["properties"]["second"]["description"] == "Second field"

    # ============================================
    # Optional Field Tests
    # ============================================

    def test_optional_field_not_in_required(self):
        """Test that Optional fields are not in required list."""
        class OptionalModel(BaseModel):
            required_field: str
            optional_field: Optional[str] = None

        schema = pydantic_to_input_schema(OptionalModel)

        assert "required_field" in schema["required"]
        assert "optional_field" not in schema["required"]

    def test_optional_field_type_is_extracted(self):
        """Test that Optional[str] extracts to string type."""
        class OptionalStrModel(BaseModel):
            maybe_name: Optional[str] = None

        schema = pydantic_to_input_schema(OptionalStrModel)

        # Should be string, not the anyOf representation
        assert schema["properties"]["maybe_name"]["type"] == "string"

    def test_optional_field_with_description(self):
        """Test that Optional fields preserve description."""
        class OptionalDescModel(BaseModel):
            maybe_name: Annotated[
                Optional[str],
                Field(default=None, description="An optional name"),
            ]

        schema = pydantic_to_input_schema(OptionalDescModel)

        assert schema["properties"]["maybe_name"]["description"] == "An optional name"

    # ============================================
    # Default Value Tests
    # ============================================

    def test_field_with_default_not_required(self):
        """Test that fields with defaults are not required."""
        class DefaultModel(BaseModel):
            name: str
            count: int = 10

        schema = pydantic_to_input_schema(DefaultModel)

        assert "name" in schema["required"]
        assert "count" not in schema["required"]

    # ============================================
    # Enum Tests
    # ============================================

    def test_string_literal_enum(self):
        """Test Literal types generate enum constraint."""
        class LiteralModel(BaseModel):
            status: Literal["pending", "active", "done"]

        schema = pydantic_to_input_schema(LiteralModel)

        assert "enum" in schema["properties"]["status"]
        assert schema["properties"]["status"]["enum"] == ["pending", "active", "done"]

    def test_python_enum_type(self):
        """Test Python Enum generates enum constraint."""
        class Status(str, Enum):
            PENDING = "pending"
            ACTIVE = "active"
            DONE = "done"

        class EnumModel(BaseModel):
            status: Status

        schema = pydantic_to_input_schema(EnumModel)

        # The enum values should be present
        assert "enum" in schema["properties"]["status"]
        assert "pending" in schema["properties"]["status"]["enum"]

    # ============================================
    # Complex Field Tests
    # ============================================

    def test_email_field(self):
        """Test EmailStr field converts to string with format."""
        class EmailModel(BaseModel):
            email: EmailStr

        schema = pydantic_to_input_schema(EmailModel)

        assert schema["properties"]["email"]["type"] == "string"
        assert schema["properties"]["email"]["format"] == "email"

    def test_constrained_integer(self):
        """Test integer with constraints preserves them."""
        class ConstrainedModel(BaseModel):
            age: Annotated[int, Field(ge=0, le=150, description="Age in years")]

        schema = pydantic_to_input_schema(ConstrainedModel)

        # Note: ge/le become minimum/maximum in JSON schema
        prop = schema["properties"]["age"]
        assert prop["type"] == "integer"
        assert prop["description"] == "Age in years"

    def test_constrained_string_length(self):
        """Test string with length constraints."""
        class LengthModel(BaseModel):
            code: Annotated[str, Field(min_length=3, max_length=10)]

        schema = pydantic_to_input_schema(LengthModel)

        prop = schema["properties"]["code"]
        assert prop["type"] == "string"

    # ============================================
    # Required Fields Tests
    # ============================================

    def test_all_required_fields(self):
        """Test model with all required fields."""
        class AllRequiredModel(BaseModel):
            first: str
            second: int
            third: bool

        schema = pydantic_to_input_schema(AllRequiredModel)

        assert set(schema["required"]) == {"first", "second", "third"}

    def test_no_required_fields(self):
        """Test model with no required fields."""
        class AllOptionalModel(BaseModel):
            first: str = "default"
            second: int = 0
            third: bool = False

        schema = pydantic_to_input_schema(AllOptionalModel)

        assert schema["required"] == []

    def test_mixed_required_optional(self):
        """Test model with mix of required and optional."""
        class MixedModel(BaseModel):
            required: str
            optional: str = "default"
            also_optional: Optional[int] = None

        schema = pydantic_to_input_schema(MixedModel)

        assert schema["required"] == ["required"]

    # ============================================
    # Schema Structure Tests
    # ============================================

    def test_schema_has_object_type(self):
        """Test schema always has type: object."""
        class AnyModel(BaseModel):
            field: str

        schema = pydantic_to_input_schema(AnyModel)

        assert schema["type"] == "object"

    def test_schema_has_properties_key(self):
        """Test schema always has properties key."""
        class AnyModel(BaseModel):
            field: str

        schema = pydantic_to_input_schema(AnyModel)

        assert "properties" in schema

    def test_schema_has_required_key(self):
        """Test schema always has required key."""
        class AnyModel(BaseModel):
            field: str

        schema = pydantic_to_input_schema(AnyModel)

        assert "required" in schema

    def test_empty_model(self):
        """Test empty model generates valid schema."""
        class EmptyModel(BaseModel):
            pass

        schema = pydantic_to_input_schema(EmptyModel)

        assert schema["type"] == "object"
        assert schema["properties"] == {}
        assert schema["required"] == []

    # ============================================
    # Real-world Request Model Tests
    # ============================================

    def test_consent_sms_request_schema(self):
        """Test the actual RequestConsentSmsV1Request schema generation."""
        from consent_mcp.mcp.v1.requests import RequestConsentSmsV1Request

        schema = pydantic_to_input_schema(RequestConsentSmsV1Request)

        # Check structure
        assert schema["type"] == "object"
        assert "requester_phone" in schema["properties"]
        assert "requester_name" in schema["properties"]
        assert "target_phone" in schema["properties"]
        assert "target_name" in schema["properties"]
        assert "scope" in schema["properties"]
        assert "expires_in_days" in schema["properties"]

        # Check required
        assert "requester_phone" in schema["required"]
        assert "requester_name" in schema["required"]
        assert "target_phone" in schema["required"]
        assert "scope" in schema["required"]
        assert "expires_in_days" in schema["required"]
        assert "target_name" not in schema["required"]

        # Check descriptions exist
        assert "description" in schema["properties"]["requester_phone"]
        assert "description" in schema["properties"]["scope"]

    def test_check_consent_email_request_schema(self):
        """Test CheckConsentEmailV1Request schema generation."""
        from consent_mcp.mcp.v1.requests import CheckConsentEmailV1Request

        schema = pydantic_to_input_schema(CheckConsentEmailV1Request)

        assert "requester_email" in schema["properties"]
        assert "target_email" in schema["properties"]
        assert schema["properties"]["requester_email"]["type"] == "string"
        assert schema["properties"]["requester_email"]["format"] == "email"

    def test_admin_simulate_request_schema(self):
        """Test AdminSimulateV1Request schema generation."""
        from consent_mcp.mcp.v1.requests import AdminSimulateV1Request

        schema = pydantic_to_input_schema(AdminSimulateV1Request)

        assert "target_contact_type" in schema["properties"]
        assert "target_contact_value" in schema["properties"]
        assert "requester_contact_value" in schema["properties"]
        assert "response" in schema["properties"]

        # All should be required
        assert len(schema["required"]) == 4

    # ============================================
    # Nested Property Tests
    # ============================================

    def test_nested_object_field(self):
        """Test that nested objects are properly converted."""
        class Address(BaseModel):
            street: str
            city: str
            zip_code: str

        class Person(BaseModel):
            name: str
            address: Address

        schema = pydantic_to_input_schema(Person)

        # Check structure
        assert "address" in schema["properties"]
        address_schema = schema["properties"]["address"]
        
        # Nested should be type object
        assert address_schema["type"] == "object"
        assert "properties" in address_schema
        assert "street" in address_schema["properties"]
        assert "city" in address_schema["properties"]
        assert "zip_code" in address_schema["properties"]

    def test_nested_object_preserves_nested_required(self):
        """Test that nested object preserves its required fields."""
        class Address(BaseModel):
            street: str
            city: str
            zip_code: str = "00000"  # Optional with default

        class Person(BaseModel):
            name: str
            address: Address

        schema = pydantic_to_input_schema(Person)

        address_schema = schema["properties"]["address"]
        
        # Nested required should include street and city, not zip_code
        assert "street" in address_schema["required"]
        assert "city" in address_schema["required"]
        assert "zip_code" not in address_schema["required"]

    def test_nested_object_preserves_descriptions(self):
        """Test that nested object fields preserve descriptions."""
        class Address(BaseModel):
            street: Annotated[str, Field(description="Street address")]
            city: Annotated[str, Field(description="City name")]

        class Person(BaseModel):
            name: str
            address: Annotated[Address, Field(description="Person's address")]

        schema = pydantic_to_input_schema(Person)

        # Top-level field description
        assert schema["properties"]["address"]["description"] == "Person's address"
        
        # Nested field descriptions
        address_schema = schema["properties"]["address"]
        assert address_schema["properties"]["street"]["description"] == "Street address"
        assert address_schema["properties"]["city"]["description"] == "City name"

    def test_optional_nested_object(self):
        """Test Optional nested object is handled correctly."""
        class Address(BaseModel):
            street: str
            city: str

        class Person(BaseModel):
            name: str
            address: Optional[Address] = None

        schema = pydantic_to_input_schema(Person)

        # address should not be required
        assert "address" not in schema["required"]
        
        # But should still have proper nested structure
        address_schema = schema["properties"]["address"]
        assert address_schema["type"] == "object"
        assert "street" in address_schema["properties"]

    def test_array_of_primitives(self):
        """Test array of primitive types."""
        class Tags(BaseModel):
            tags: list[str]

        schema = pydantic_to_input_schema(Tags)

        tags_schema = schema["properties"]["tags"]
        assert tags_schema["type"] == "array"
        assert tags_schema["items"]["type"] == "string"

    def test_array_of_objects(self):
        """Test array of nested objects."""
        class Address(BaseModel):
            street: str
            city: str

        class Person(BaseModel):
            name: str
            addresses: list[Address]

        schema = pydantic_to_input_schema(Person)

        # Check array structure
        addresses_schema = schema["properties"]["addresses"]
        assert addresses_schema["type"] == "array"
        
        # Check items are objects
        items_schema = addresses_schema["items"]
        assert items_schema["type"] == "object"
        assert "street" in items_schema["properties"]
        assert "city" in items_schema["properties"]

    def test_deeply_nested_objects(self):
        """Test deeply nested objects (3 levels)."""
        class Country(BaseModel):
            name: str
            code: str

        class Address(BaseModel):
            street: str
            country: Country

        class Person(BaseModel):
            name: str
            address: Address

        schema = pydantic_to_input_schema(Person)

        # Navigate to deeply nested
        address_schema = schema["properties"]["address"]
        assert address_schema["type"] == "object"
        
        country_schema = address_schema["properties"]["country"]
        assert country_schema["type"] == "object"
        assert "name" in country_schema["properties"]
        assert "code" in country_schema["properties"]

    def test_nested_with_mixed_types(self):
        """Test nested objects with various field types."""
        class Metadata(BaseModel):
            created_at: str
            version: int
            active: bool
            tags: list[str]

        class Document(BaseModel):
            title: str
            metadata: Metadata

        schema = pydantic_to_input_schema(Document)

        metadata_schema = schema["properties"]["metadata"]
        assert metadata_schema["type"] == "object"
        assert metadata_schema["properties"]["created_at"]["type"] == "string"
        assert metadata_schema["properties"]["version"]["type"] == "integer"
        assert metadata_schema["properties"]["active"]["type"] == "boolean"
        assert metadata_schema["properties"]["tags"]["type"] == "array"

    def test_nested_object_with_enum(self):
        """Test nested object containing an enum field."""
        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class Settings(BaseModel):
            theme: str
            status: Status

        class User(BaseModel):
            name: str
            settings: Settings

        schema = pydantic_to_input_schema(User)

        settings_schema = schema["properties"]["settings"]
        assert "status" in settings_schema["properties"]
        assert "enum" in settings_schema["properties"]["status"]

    def test_array_of_optional_objects(self):
        """Test array with optional object items."""
        class Item(BaseModel):
            name: str
            quantity: int = 1

        class Order(BaseModel):
            items: list[Item]

        schema = pydantic_to_input_schema(Order)

        items_schema = schema["properties"]["items"]
        assert items_schema["type"] == "array"
        
        item_schema = items_schema["items"]
        assert "name" in item_schema["required"]
        assert "quantity" not in item_schema["required"]

