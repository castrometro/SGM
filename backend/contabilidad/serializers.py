import logging
from rest_framework import serializers

from .models import (
    AccountClassification,
    AnalisisCuentaCierre,
    AperturaCuenta,
    Auxiliar,
    CentroCosto,
    CierreContabilidad,
    # ClasificacionCuentaArchivo,  # OBSOLETO - ELIMINADO
    ClasificacionOption,
    ClasificacionSet,
    CuentaContable,
    Incidencia,
    LibroMayorArchivo,  # ✅ Nuevo modelo
    MovimientoContable,
    NombresEnInglesUpload,
    TarjetaActivityLog,
    TipoDocumento,
)


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = "__all__"

    def validate(self, data):
        # Validar que no exista un tipo de documento con el mismo código para el mismo cliente
        cliente = data.get("cliente")
        codigo = data.get("codigo")

        if cliente and codigo:
            # En caso de actualización, excluir el registro actual
            queryset = TipoDocumento.objects.filter(cliente=cliente, codigo=codigo)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    {
                        "codigo": f'Ya existe un tipo de documento con el código "{codigo}" para este cliente.'
                    }
                )

        return data



class CuentaContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaContable
        fields = "__all__"


class CierreContabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CierreContabilidad
        fields = [
            "id",
            "cliente",
            "usuario",
            "area",
            "periodo",
            "fecha_inicio_libro",
            "fecha_fin_libro",
            "estado",
            "fecha_creacion",
            "fecha_cierre",
            "cuentas_nuevas",
            "resumen_parsing",
            "parsing_completado",
        ]
        read_only_fields = ["fecha_creacion", "fecha_cierre", "usuario"]

    def validate(self, data):
        logger = logging.getLogger('contabilidad')
        cliente = data.get("cliente")
        periodo = data.get("periodo")

        if cliente and periodo:
            logger.debug("="*80)
            logger.debug(f"VALIDATE CIERRE - Input data:")
            logger.debug(f"Cliente ID: {getattr(cliente, 'id', cliente)}")
            logger.debug(f"Cliente nombre: {getattr(cliente, 'nombre', 'N/A')}")
            logger.debug(f"Periodo: {periodo}")
            
            # Consultar todos los cierres existentes para este cliente
            all_cierres = CierreContabilidad.objects.filter(
                cliente=cliente
            ).order_by('-fecha_creacion')
            
            logger.debug(f"Cierres existentes para el cliente {getattr(cliente, 'id', cliente)}:")
            for cierre in all_cierres:
                logger.debug(f"ID: {cierre.id} | Periodo: {cierre.periodo} | Estado: {cierre.estado}")
            
            # En caso de actualización, excluir el registro actual
            queryset = CierreContabilidad.objects.filter(
                cliente=cliente, 
                periodo=periodo
            ).order_by('-fecha_creacion')
            
            if self.instance:
                logger.debug(f"Excluyendo instancia actual: {self.instance.id}")
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                cierre_existente = queryset.first()
                logger.debug(f"Cierre existente encontrado:")
                logger.debug(f"ID: {cierre_existente.id}")
                logger.debug(f"Periodo: {cierre_existente.periodo}")
                logger.debug(f"Estado: {cierre_existente.estado}")
                
                # Solo consideramos como duplicado si el cierre existente está activo
                if cierre_existente.estado not in ['cancelado', 'eliminado']:
                    logger.debug(f"Validación fallida - Cierre activo existente")
                    raise serializers.ValidationError(
                        {
                            "periodo": f'Ya existe un cierre contable activo para el cliente "{cliente.nombre}" en el periodo "{periodo}". Estado actual: {cierre_existente.get_estado_display()}.'
                        }
                    )
                else:
                    logger.debug(f"Cierre existente está {cierre_existente.estado}, permitiendo crear nuevo")
            else:
                logger.debug(f"No se encontró cierre existente para el periodo {periodo}")
            
            logger.debug("="*80)

        return data


class ProgresoClasificacionSerializer(serializers.Serializer):
    existen_sets = serializers.BooleanField()
    cuentas_nuevas = serializers.IntegerField()
    total_cuentas = serializers.IntegerField()
    parsing_completado = serializers.BooleanField()



class LibroMayorArchivoSerializer(serializers.ModelSerializer):
    """Serializer para el nuevo modelo LibroMayorArchivo que persiste entre cierres"""
    archivo_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = LibroMayorArchivo
        fields = [
            "id",
            "cliente",
            "archivo", 
            "archivo_nombre",
            "fecha_subida",
            "periodo",
            "procesado",
            "errores",
            "estado",
            "upload_log",
        ]
        read_only_fields = ["fecha_subida", "procesado", "errores", "estado", "upload_log", "archivo_nombre"]
    
    def get_archivo_nombre(self, obj):
        """Extrae el nombre del archivo del path completo"""
        if obj.archivo:
            import os
            return os.path.basename(obj.archivo.name)
        return None


class AperturaCuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AperturaCuenta
        fields = "__all__"


class MovimientoContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoContable
        fields = "__all__"


class ClasificacionSetSerializer(serializers.ModelSerializer):
    tiene_opciones_bilingues = serializers.SerializerMethodField()
    total_opciones = serializers.SerializerMethodField()
    
    class Meta:
        model = ClasificacionSet
        fields = "__all__"
        
    def get_tiene_opciones_bilingues(self, obj):
        """Verificar si el set tiene opciones con contenido en ambos idiomas"""
        for opcion in obj.opciones.all():
            tiene_es = bool(opcion.valor and opcion.valor.strip())
            tiene_en = bool(opcion.valor_en and opcion.valor_en.strip())
            if tiene_es and tiene_en:
                return True
        return False
        
    def get_total_opciones(self, obj):
        """Obtener el total de opciones del set"""
        return obj.opciones.count()


class ClasificacionOptionSerializer(serializers.ModelSerializer):
    # Campos bilingües adicionales para lectura
    valor_es = serializers.SerializerMethodField()
    descripcion_es = serializers.SerializerMethodField()
    tiene_es = serializers.SerializerMethodField()
    tiene_en = serializers.SerializerMethodField()
    es_bilingue = serializers.SerializerMethodField()
    
    class Meta:
        model = ClasificacionOption
        fields = "__all__"
        
    def create(self, validated_data):
        """
        Crear una nueva opción de clasificación con soporte bilingüe completo.
        UPDATED: Forzar recarga con logging detallado
        """
        print(f"🔧 ClasificacionOptionSerializer.create() - Datos recibidos: {validated_data}")
        
        # Extraer todos los campos bilingües
        valor = validated_data.get('valor', '')
        valor_en = validated_data.get('valor_en', '')
        descripcion = validated_data.get('descripcion', '')
        descripcion_en = validated_data.get('descripcion_en', '')
        
        print(f"   📝 Campos extraídos:")
        print(f"      valor (ES): '{valor}'")
        print(f"      valor_en (EN): '{valor_en}'")
        print(f"      descripcion (ES): '{descripcion}'")
        print(f"      descripcion_en (EN): '{descripcion_en}'")
        
        # Crear la instancia
        instance = ClasificacionOption.objects.create(**validated_data)
        
        print(f"   ✅ Instancia creada con ID: {instance.id}")
        print(f"   🔍 Valores guardados en DB:")
        print(f"      instance.valor: '{instance.valor}'")
        print(f"      instance.valor_en: '{instance.valor_en}'")
        print(f"      instance.descripcion: '{instance.descripcion}'")
        print(f"      instance.descripcion_en: '{instance.descripcion_en}'")
        
        return instance
        
    def update(self, instance, validated_data):
        """
        Actualizar una opción de clasificación con soporte bilingüe completo.
        """
        print(f"🔧 ClasificacionOptionSerializer.update() - Datos recibidos: {validated_data}")
        print(f"   📋 Instancia actual ID: {instance.id}")
        
        # Actualizar todos los campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            print(f"      {attr}: '{value}'")
            
        instance.save()
        
        print(f"   ✅ Instancia actualizada")
        print(f"   🔍 Valores finales en DB:")
        print(f"      instance.valor: '{instance.valor}'")
        print(f"      instance.valor_en: '{instance.valor_en}'")
        print(f"      instance.descripcion: '{instance.descripcion}'")
        print(f"      instance.descripcion_en: '{instance.descripcion_en}'")
        
        return instance
        
    def get_valor_es(self, obj):
        """Obtener valor en español"""
        return obj.valor
        
    def get_descripcion_es(self, obj):
        """Obtener descripción en español"""
        return obj.descripcion
        
    def get_tiene_es(self, obj):
        """Verificar si tiene contenido en español"""
        return bool(obj.valor and obj.valor.strip())
        
    def get_tiene_en(self, obj):
        """Verificar si tiene contenido en inglés"""
        return bool(obj.valor_en and obj.valor_en.strip())
        
    def get_es_bilingue(self, obj):
        """Verificar si la opción tiene contenido en ambos idiomas"""
        return self.get_tiene_es(obj) and self.get_tiene_en(obj)


class AccountClassificationSerializer(serializers.ModelSerializer):
    # Campos adicionales para mostrar información detallada
    cuenta_codigo = serializers.CharField(source="cuenta.codigo", read_only=True)
    cuenta_nombre = serializers.CharField(source="cuenta.nombre", read_only=True)
    set_nombre = serializers.CharField(source="set_clas.nombre", read_only=True)
    opcion_valor = serializers.CharField(source="opcion.valor", read_only=True)
    opcion_descripcion = serializers.CharField(
        source="opcion.descripcion", read_only=True
    )
    asignado_por_nombre = serializers.CharField(
        source="asignado_por.nombre", read_only=True
    )

    class Meta:
        model = AccountClassification
        fields = [
            "id",
            "cuenta",
            "set_clas",
            "opcion",
            "asignado_por",
            "fecha",
            "cuenta_codigo",
            "cuenta_nombre",
            "set_nombre",
            "opcion_valor",
            "opcion_descripcion",
            "asignado_por_nombre",
        ]


class AnalisisCuentaCierreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalisisCuentaCierre
        fields = "__all__"


class IncidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incidencia
        fields = "__all__"


class CentroCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroCosto
        fields = "__all__"


class AuxiliarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auxiliar
        fields = "__all__"


# ======================================
#     SERIALIZER OBSOLETO - ELIMINADO
# ======================================

# class ClasificacionCuentaArchivoSerializer(serializers.ModelSerializer):
#     """
#     OBSOLETO: Este serializer será eliminado.
#     Ahora AccountClassification es la fuente única de verdad.
#     """
#     pass


class NombresEnInglesUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = NombresEnInglesUpload
        fields = [
            "id",
            "cliente",
            "cierre",
            "archivo",
            "fecha_subida",
            "estado",
            "errores",
            "resumen",
        ]


class TarjetaActivityLogSerializer(serializers.ModelSerializer):
    tarjeta_display = serializers.CharField(
        source="get_tarjeta_display", read_only=True
    )
    accion_display = serializers.CharField(source="get_accion_display", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)
    cliente_nombre = serializers.CharField(
        source="cierre.cliente.nombre", read_only=True
    )

    class Meta:
        model = TarjetaActivityLog
        fields = [
            "id",
            "cierre",
            "tarjeta",
            "tarjeta_display",
            "accion",
            "accion_display",
            "usuario",
            "usuario_nombre",
            "cliente_nombre",
            "descripcion",
            "detalles",
            "resultado",
            "timestamp",
            "ip_address",
        ]
        read_only_fields = ["timestamp"]
