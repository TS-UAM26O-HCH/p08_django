from rest_framework import serializers
from .models import Usuario


class UsuarioParcialSerializer(serializers.ModelSerializer):
    """Serializador utilizado para la creación y actualización parcial de usuarios."""

    class Meta:
        model = Usuario
        fields = [
            "username",
            "password",
            "date_of_birth",
            "first_name",
            "last_name",
            "email",
        ]

        extra_kwargs = {field: {"required": False} for field in fields}
        extra_kwargs["password"] = {"required": False, "write_only": True}

    @staticmethod
    def validar_username(username):
        """Valida que el username no tenga más de 20 caracteres."""
        if len(username) > 20:
            raise serializers.ValidationError(
                "El nombre de usuario no puede tener más de 20 caracteres."
            )
        return username


class UsuarioCompletoSerializer(serializers.ModelSerializer):
    """Serializador para actualizar completamente un usuario (PUT)."""

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "password",
            "date_of_birth",
            "first_name",
            "last_name",
            "email",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_username(self, username):
        if len(username) > 20:
            raise serializers.ValidationError(
                "El nombre de usuario no puede tener más de 20 caracteres."
            )
        return username


class UsuarioContrasenaSerializer(serializers.ModelSerializer):
    """Serializador para actualizar la contraseña."""

    # Campos temporales para las contraseñas
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ["current_password", "new_password", "confirm_password"]
        extra_kwargs = {field: {"required": True} for field in fields}

    def validate(self, data):
        """Valida que la nueva contraseña coincida con la confirmación y tenga longitud mínima."""
        if len(data["new_password"]) < 8:
            raise serializers.ValidationError(
                "La nueva contraseña debe contener al menos 8 caracteres."
            )
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializador para solicitar el restablecimiento de contraseña."""

    email = serializers.EmailField()
