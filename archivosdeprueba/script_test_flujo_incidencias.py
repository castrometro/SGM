#!/usr/bin/env python3
# script_test_flujo_incidencias.py
"""
Script para validar el flujo completo de incidencias después de las correcciones.
Incluye:
1. Verificación de endpoints de caché
2. Simulación de reprocesamiento
3. Validación de datos actualizados en modal
4. Test de permisos de usuario
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000/api"
USERNAME = "test_user"  # Ajustar según tu configuración
PASSWORD = "test_pass"  # Ajustar según tu configuración

class TestFlowIncidencias:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def login(self):
        """Autenticación"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login/", {
                'username': USERNAME,
                'password': PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print("✓ Login exitoso")
                return True
            else:
                print(f"✗ Error de login: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error de conexión: {e}")
            return False
    
    def test_cache_endpoints(self):
        """Test de endpoints de caché"""
        print("\n=== TEST ENDPOINTS DE CACHÉ ===")
        
        # Test estado del caché
        try:
            response = self.session.get(f"{BASE_URL}/contabilidad/incidencias/estado-cache/")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Estado de caché obtenido: {data.get('cache_activo', 'N/A')} claves activas")
            else:
                print(f"✗ Error obteniendo estado de caché: {response.status_code}")
        except Exception as e:
            print(f"✗ Error en estado de caché: {e}")
        
        # Test limpiar caché
        try:
            response = self.session.post(f"{BASE_URL}/contabilidad/incidencias/limpiar-cache/")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Caché limpiado: {data.get('mensaje', 'Sin mensaje')}")
            else:
                print(f"✗ Error limpiando caché: {response.status_code}")
        except Exception as e:
            print(f"✗ Error limpiando caché: {e}")
    
    def test_incidencias_flow(self, cierre_id=1):
        """Test del flujo principal de incidencias"""
        print(f"\n=== TEST FLUJO INCIDENCIAS (Cierre {cierre_id}) ===")
        
        # 1. Obtener incidencias sin forzar actualización
        try:
            response = self.session.get(
                f"{BASE_URL}/contabilidad/incidencias/consolidadas/{cierre_id}/"
            )
            if response.status_code == 200:
                data1 = response.json()
                print(f"✓ Incidencias obtenidas (cache): {len(data1.get('incidencias', []))} incidencias")
            else:
                print(f"✗ Error obteniendo incidencias: {response.status_code}")
                return
        except Exception as e:
            print(f"✗ Error en flujo incidencias: {e}")
            return
        
        # 2. Obtener incidencias forzando actualización
        try:
            response = self.session.get(
                f"{BASE_URL}/contabilidad/incidencias/consolidadas/{cierre_id}/?forzar_actualizacion=true"
            )
            if response.status_code == 200:
                data2 = response.json()
                print(f"✓ Incidencias obtenidas (live): {len(data2.get('incidencias', []))} incidencias")
                
                # Comparar metadatos
                meta1 = data1.get('metadatos', {})
                meta2 = data2.get('metadatos', {})
                print(f"  - Fuente cache: {meta1.get('fuente_datos', 'N/A')}")
                print(f"  - Fuente live: {meta2.get('fuente_datos', 'N/A')}")
                
            else:
                print(f"✗ Error obteniendo incidencias live: {response.status_code}")
        except Exception as e:
            print(f"✗ Error en flujo incidencias live: {e}")
    
    def test_marcar_resuelta(self, incidencia_id=None):
        """Test marcar incidencia como resuelta"""
        if not incidencia_id:
            print("\n=== SKIP TEST MARCAR RESUELTA (sin ID) ===")
            return
            
        print(f"\n=== TEST MARCAR RESUELTA (ID {incidencia_id}) ===")
        
        try:
            response = self.session.post(
                f"{BASE_URL}/contabilidad/incidencias/{incidencia_id}/marcar-resuelta/"
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Incidencia marcada como resuelta: {data.get('mensaje', 'Sin mensaje')}")
            else:
                print(f"✗ Error marcando como resuelta: {response.status_code}")
                if response.content:
                    try:
                        error_data = response.json()
                        print(f"  Error: {error_data}")
                    except:
                        print(f"  Error: {response.text}")
        except Exception as e:
            print(f"✗ Error en marcar resuelta: {e}")
    
    def test_user_permissions(self):
        """Test de permisos de usuario"""
        print("\n=== TEST PERMISOS DE USUARIO ===")
        
        # Verificar que el usuario esté correctamente autenticado
        if self.token:
            print("✓ Token de autenticación presente")
        else:
            print("✗ Sin token de autenticación")
            return
        
        # Test endpoint que requiere permisos
        try:
            response = self.session.get(f"{BASE_URL}/contabilidad/incidencias/estado-cache/")
            if response.status_code == 200:
                print("✓ Permisos de usuario validados")
            elif response.status_code == 403:
                print("✗ Permisos insuficientes")
            else:
                print(f"✗ Error de permisos: {response.status_code}")
        except Exception as e:
            print(f"✗ Error validando permisos: {e}")
    
    def run_full_test(self, cierre_id=1, incidencia_id=None):
        """Ejecutar suite completa de tests"""
        print("=" * 50)
        print("INICIANDO TESTS DE FLUJO DE INCIDENCIAS")
        print("=" * 50)
        
        if not self.login():
            print("✗ FALLÓ LOGIN - ABORTANDO TESTS")
            return
        
        self.test_user_permissions()
        self.test_cache_endpoints()
        self.test_incidencias_flow(cierre_id)
        
        if incidencia_id:
            self.test_marcar_resuelta(incidencia_id)
        
        print("\n" + "=" * 50)
        print("TESTS COMPLETADOS")
        print("=" * 50)

if __name__ == "__main__":
    tester = TestFlowIncidencias()
    
    # Configurar parámetros según tu entorno
    CIERRE_ID = 1  # Ajustar según tu DB
    INCIDENCIA_ID = None  # Poner un ID válido si quieres testear marcar como resuelta
    
    tester.run_full_test(cierre_id=CIERRE_ID, incidencia_id=INCIDENCIA_ID)
