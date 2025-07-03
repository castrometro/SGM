/**
 * Componente React para el botón "Finalizar Cierre y Generar Reportes"
 * 
 * Este componente:
 * 1. Muestra el botón solo cuando el cierre está en estado "sin_incidencias"
 * 2. Maneja la finalización del cierre
 * 3. Muestra el progreso de la tarea de Celery
 * 4. Actualiza el estado en tiempo real
 */

import React, { useState, useEffect } from 'react';
import { Button, Card, Progress, Alert, Modal, Spin } from 'antd';
import { CheckCircleOutlined, LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';

const FinalizarCierreComponent = ({ cierre, onCierreActualizado }) => {
    const [finalizando, setFinalizando] = useState(false);
    const [taskId, setTaskId] = useState(null);
    const [progreso, setProgreso] = useState(null);
    const [error, setError] = useState(null);
    const [modalVisible, setModalVisible] = useState(false);

    // Polling para verificar el progreso de la tarea
    useEffect(() => {
        let interval;
        
        if (taskId && finalizando) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/contabilidad/tareas/${taskId}/progreso/`);
                    const data = await response.json();
                    
                    if (data.estado === 'SUCCESS') {
                        setFinalizando(false);
                        setProgreso(data.resultado);
                        onCierreActualizado(); // Callback para refrescar el cierre
                        setModalVisible(false);
                        
                        // Mostrar notificación de éxito
                        notification.success({
                            message: 'Cierre Finalizado',
                            description: 'El cierre ha sido finalizado exitosamente y los reportes han sido generados.',
                            duration: 5
                        });
                        
                    } else if (data.estado === 'FAILURE') {
                        setFinalizando(false);
                        setError(data.error || 'Error desconocido en la finalización');
                        
                    } else if (data.progreso) {
                        setProgreso(data.progreso);
                    }
                } catch (err) {
                    console.error('Error al verificar progreso:', err);
                }
            }, 2000); // Verificar cada 2 segundos
        }
        
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [taskId, finalizando]);

    const puedeFinalizarCierre = () => {
        return cierre.estado === 'sin_incidencias';
    };

    const iniciarFinalizacion = async () => {
        setError(null);
        setFinalizando(true);
        setModalVisible(true);
        
        try {
            const response = await fetch(`/api/contabilidad/cierres/${cierre.id}/finalizar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                setTaskId(data.task_id);
                setProgreso({
                    descripcion: 'Iniciando finalización...',
                    porcentaje: 0
                });
            } else {
                setFinalizando(false);
                setError(data.error);
                setModalVisible(false);
            }
        } catch (err) {
            setFinalizando(false);
            setError('Error de conexión al servidor');
            setModalVisible(false);
        }
    };

    const confirmarFinalizacion = () => {
        Modal.confirm({
            title: '¿Confirmar Finalización del Cierre?',
            content: (
                <div>
                    <p>Esta acción finalizará el cierre contable y generará todos los reportes.</p>
                    <p><strong>Período:</strong> {cierre.periodo}</p>
                    <p><strong>Cliente:</strong> {cierre.cliente}</p>
                    <p>El proceso tomará aproximadamente 2-5 minutos.</p>
                </div>
            ),
            icon: <ExclamationCircleOutlined />,
            okText: 'Sí, Finalizar',
            okType: 'primary',
            cancelText: 'Cancelar',
            onOk: iniciarFinalizacion,
        });
    };

    const renderProgreso = () => {
        if (!progreso) return null;

        return (
            <div style={{ padding: '20px' }}>
                <div style={{ marginBottom: '16px' }}>
                    <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
                    <span style={{ marginLeft: '12px', fontSize: '16px' }}>
                        {progreso.descripcion || 'Procesando...'}
                    </span>
                </div>
                
                {progreso.porcentaje !== undefined && (
                    <Progress 
                        percent={progreso.porcentaje} 
                        status="active"
                        strokeColor={{
                            '0%': '#108ee9',
                            '100%': '#87d068',
                        }}
                    />
                )}
                
                {progreso.paso_actual && progreso.total_pasos && (
                    <div style={{ marginTop: '8px', color: '#666' }}>
                        Paso {progreso.paso_actual} de {progreso.total_pasos}
                    </div>
                )}
            </div>
        );
    };

    if (cierre.estado === 'finalizado') {
        return (
            <Card 
                size="small" 
                style={{ 
                    backgroundColor: '#f6ffed', 
                    borderColor: '#b7eb8f',
                    marginTop: '16px'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                    <span>
                        <strong>Cierre Finalizado</strong>
                        {cierre.fecha_finalizacion && (
                            <span style={{ marginLeft: '8px', color: '#666' }}>
                                el {new Date(cierre.fecha_finalizacion).toLocaleDateString()}
                            </span>
                        )}
                    </span>
                </div>
                
                {cierre.reportes_generados && (
                    <div style={{ marginTop: '8px' }}>
                        <Button type="link" size="small">
                            Descargar Reportes
                        </Button>
                    </div>
                )}
            </Card>
        );
    }

    if (cierre.estado === 'generando_reportes') {
        return (
            <Card 
                size="small" 
                style={{ 
                    backgroundColor: '#fff7e6', 
                    borderColor: '#ffd666',
                    marginTop: '16px'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Spin size="small" style={{ marginRight: '8px' }} />
                    <span>
                        <strong>Generando Reportes...</strong>
                    </span>
                </div>
                <div style={{ marginTop: '8px', color: '#666' }}>
                    El cierre se está finalizando. Este proceso puede tomar varios minutos.
                </div>
            </Card>
        );
    }

    if (!puedeFinalizarCierre()) {
        return (
            <Card 
                size="small" 
                style={{ 
                    backgroundColor: '#fff2f0', 
                    borderColor: '#ffccc7',
                    marginTop: '16px'
                }}
            >
                <div style={{ color: '#666' }}>
                    El cierre debe estar en estado "Sin Incidencias" para poder ser finalizado.
                </div>
            </Card>
        );
    }

    return (
        <>
            <Card 
                size="small" 
                style={{ 
                    backgroundColor: '#e6f7ff', 
                    borderColor: '#91d5ff',
                    marginTop: '16px'
                }}
            >
                <div style={{ textAlign: 'center' }}>
                    <div style={{ marginBottom: '12px' }}>
                        <strong>¡Cierre listo para finalizar!</strong>
                    </div>
                    <div style={{ marginBottom: '16px', color: '#666' }}>
                        Todas las incidencias han sido resueltas. 
                        Puedes proceder a finalizar el cierre y generar los reportes.
                    </div>
                    
                    <Button
                        type="primary"
                        size="large"
                        onClick={confirmarFinalizacion}
                        disabled={finalizando}
                        icon={<CheckCircleOutlined />}
                        style={{
                            height: '48px',
                            fontSize: '16px',
                            fontWeight: 'bold'
                        }}
                    >
                        Finalizar Cierre y Generar Reportes
                    </Button>
                </div>
                
                {error && (
                    <Alert
                        message="Error en Finalización"
                        description={error}
                        type="error"
                        style={{ marginTop: '16px' }}
                        closable
                        onClose={() => setError(null)}
                    />
                )}
            </Card>

            {/* Modal de progreso */}
            <Modal
                title="Finalizando Cierre Contable"
                visible={modalVisible}
                footer={null}
                closable={false}
                width={500}
            >
                {renderProgreso()}
                
                <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                        <strong>Proceso incluye:</strong>
                    </div>
                    <ul style={{ fontSize: '12px', color: '#666', marginBottom: 0 }}>
                        <li>Validaciones finales de integridad</li>
                        <li>Cálculos contables y balance</li>
                        <li>Consolidación para dashboard</li>
                        <li>Generación de reportes</li>
                        <li>Finalización del cierre</li>
                    </ul>
                </div>
            </Modal>
        </>
    );
};

export default FinalizarCierreComponent;
