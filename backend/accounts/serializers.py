import re

from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.models import Menu, Permission, Role, UserAccessProfile, UserRole, UserSalesScope
from projects.models import Person


UNSET = object()


class PersonBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "name", "person_type", "position", "phone", "email"]


class RoleBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "code", "status"]


class UserAccessProfileSerializer(serializers.ModelSerializer):
    bound_person = serializers.SerializerMethodField()
    sales_scope = serializers.SerializerMethodField()

    class Meta:
        model = UserAccessProfile
        fields = ["id", "data_scope_type", "remark", "status", "bound_person", "sales_scope"]

    def get_bound_person(self, obj):
        person = getattr(obj.user, "person_profile", None)
        return PersonBriefSerializer(person).data if person else None

    def get_sales_scope(self, obj):
        sales_people = [item.sales_person for item in obj.sales_scopes.select_related("sales_person")]
        return PersonBriefSerializer(sales_people, many=True).data


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    role_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), write_only=True, required=False)
    bound_person_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    data_scope_type = serializers.ChoiceField(choices=UserAccessProfile.DATA_SCOPE_CHOICES, write_only=True, required=False)
    sales_scope_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), write_only=True, required=False)
    roles = serializers.SerializerMethodField()
    access_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "password",
            "role_ids",
            "bound_person_id",
            "data_scope_type",
            "sales_scope_ids",
            "roles",
            "access_profile",
        ]

    def validate_role_ids(self, value):
        role_count = Role.objects.filter(id__in=value).count()
        if role_count != len(set(value)):
            raise serializers.ValidationError("存在无效角色")
        return list(dict.fromkeys(value))

    def validate_sales_scope_ids(self, value):
        sales_people = Person.objects.filter(id__in=value, person_type="sales")
        if sales_people.count() != len(set(value)):
            raise serializers.ValidationError("销售范围中存在无效销售人员")
        return list(dict.fromkeys(value))

    def validate(self, attrs):
        bound_person = self._resolve_bound_person(attrs)
        if bound_person and bound_person.user_id and (not self.instance or bound_person.user_id != self.instance.id):
            raise serializers.ValidationError({"bound_person_id": "该人员已绑定其他账号"})

        scope_type = attrs.get("data_scope_type", getattr(getattr(self.instance, "access_profile", None), "data_scope_type", None))
        sales_scope_ids = attrs.get("sales_scope_ids", None)

        if scope_type == UserAccessProfile.DATA_SCOPE_SELF:
            if not bound_person or bound_person.person_type != "sales":
                raise serializers.ValidationError({"data_scope_type": "本人数据范围要求绑定销售人员"})
        if scope_type == UserAccessProfile.DATA_SCOPE_CUSTOM and sales_scope_ids is not None and not sales_scope_ids:
            raise serializers.ValidationError({"sales_scope_ids": "自定义范围至少选择一名销售"})
        return attrs

    def create(self, validated_data):
        extras = self._pop_extra_fields(validated_data)
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        self._apply_extra_settings(user, extras)
        return user

    def update(self, instance, validated_data):
        extras = self._pop_extra_fields(validated_data)
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        self._apply_extra_settings(instance, extras)
        return instance

    def get_roles(self, obj):
        roles = [item.role for item in obj.user_roles.select_related("role")]
        return RoleBriefSerializer(roles, many=True).data

    def get_access_profile(self, obj):
        if obj.is_superuser:
            return {
                "data_scope_type": UserAccessProfile.DATA_SCOPE_ALL,
                "bound_person": PersonBriefSerializer(getattr(obj, "person_profile", None)).data if hasattr(obj, "person_profile") else None,
                "sales_scope": [],
            }
        profile = getattr(obj, "access_profile", None)
        return UserAccessProfileSerializer(profile).data if profile else None

    def _resolve_bound_person(self, attrs):
        bound_person_id = attrs.get("bound_person_id", UNSET)
        if bound_person_id is UNSET:
            return getattr(self.instance, "person_profile", None) if self.instance else None
        if bound_person_id is None:
            return None
        person = Person.objects.filter(id=bound_person_id).first()
        if not person:
            raise serializers.ValidationError({"bound_person_id": "绑定人员不存在"})
        return person

    def _pop_extra_fields(self, validated_data):
        return {
            "role_ids": validated_data.pop("role_ids", UNSET),
            "bound_person_id": validated_data.pop("bound_person_id", UNSET),
            "data_scope_type": validated_data.pop("data_scope_type", UNSET),
            "sales_scope_ids": validated_data.pop("sales_scope_ids", UNSET),
        }

    def _apply_extra_settings(self, user, extras):
        self._sync_roles(user, extras["role_ids"])
        self._sync_bound_person(user, extras["bound_person_id"])
        self._sync_access_profile(user, extras["data_scope_type"], extras["sales_scope_ids"])

    def _sync_roles(self, user, role_ids):
        if role_ids is UNSET:
            return
        UserRole.objects.filter(user=user).exclude(role_id__in=role_ids).delete()
        existing_ids = set(UserRole.objects.filter(user=user).values_list("role_id", flat=True))
        UserRole.objects.bulk_create([
            UserRole(user=user, role_id=role_id)
            for role_id in role_ids
            if role_id not in existing_ids
        ])

    def _sync_bound_person(self, user, bound_person_id):
        if bound_person_id is UNSET:
            return
        current_person = Person.objects.filter(user=user).first()
        if current_person and (bound_person_id is None or current_person.id != bound_person_id):
            current_person.user = None
            current_person.save(update_fields=["user"])
        if bound_person_id is None:
            return
        person = Person.objects.get(id=bound_person_id)
        if person.user_id != user.id:
            person.user = user
            person.save(update_fields=["user"])

    def _sync_access_profile(self, user, data_scope_type, sales_scope_ids):
        if data_scope_type is UNSET and sales_scope_ids is UNSET:
            return
        profile, _ = UserAccessProfile.objects.get_or_create(user=user)
        if data_scope_type is not UNSET:
            profile.data_scope_type = data_scope_type
        profile.save()

        if sales_scope_ids is UNSET:
            return
        if profile.data_scope_type != UserAccessProfile.DATA_SCOPE_CUSTOM:
            UserSalesScope.objects.filter(profile=profile).delete()
            return
        UserSalesScope.objects.filter(profile=profile).exclude(sales_person_id__in=sales_scope_ids).delete()
        existing_ids = set(UserSalesScope.objects.filter(profile=profile).values_list("sales_person_id", flat=True))
        UserSalesScope.objects.bulk_create([
            UserSalesScope(profile=profile, sales_person_id=sales_person_id)
            for sales_person_id in sales_scope_ids
            if sales_person_id not in existing_ids
        ])


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ["id", "name", "code", "path", "parent", "icon", "order_index", "status"]


class RoleSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False, allow_blank=True)
    permission_pairs = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "code", "remark", "status", "created_at", "updated_at", "permission_pairs"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        code = (attrs.get("code") or "").strip()
        if not code:
            attrs["code"] = self._generate_role_code(attrs.get("name") or getattr(self.instance, "name", "role"))
        return attrs

    def get_permission_pairs(self, obj):
        return list(obj.permissions.values_list("menu_id", "action"))

    def _generate_role_code(self, name):
        normalized = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
        base = f"role-{normalized}" if normalized else "role-1"
        candidate = base
        index = 1
        queryset = Role.objects.all()
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        existing_codes = set(queryset.values_list("code", flat=True))
        while candidate in existing_codes:
            index += 1
            candidate = f"{base}-{index}"
        return candidate


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "role", "menu", "action"]


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ["id", "user", "role"]
