import React, { useState } from 'react';
import { Container, Row, Col, Card, Button, Alert, Form } from 'react-bootstrap';
import { useAuth } from '../hooks/useAuth';

const DashboardStreamlitAccess = ({ clienteId, clienteNombre }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const { token } = useAuth();

    const abrirDashboardContable = async () => {
        if (!clienteId) {
            setError('ID de cliente requerido');
            return;
        }

        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const response = await fetch('/api/dashboard-streamlit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    cliente_id: clienteId
                })
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess(`Dashboard preparado para ${data.cliente.nombre}`);
                
                // Abrir en nueva pestaña
                window.open(data.streamlit_url, '_blank');
            } else {
                setError(data.error || 'Error al acceder al dashboard');
            }
        } catch (err) {
            setError('Error de conexión al servidor');
        } finally {
            setLoading(false);
        }
    };

    const abrirDashboardDirecto = () => {
        if (!clienteId) {
            setError('ID de cliente requerido');
            return;
        }

        // Abrir directamente con GET (redireccionamiento automático)
        const url = `/api/dashboard-streamlit/${clienteId}/`;
        window.open(url, '_blank');
    };

    return (
        <Card className="mb-3">
            <Card.Header className="bg-primary text-white">
                <h5 className="mb-0">
                    📊 Dashboard Contable - {clienteNombre || `Cliente ${clienteId}`}
                </h5>
            </Card.Header>
            <Card.Body>
                {error && (
                    <Alert variant="danger" className="mb-3">
                        {error}
                    </Alert>
                )}
                
                {success && (
                    <Alert variant="success" className="mb-3">
                        {success}
                    </Alert>
                )}

                <Row>
                    <Col md={6}>
                        <div className="d-grid gap-2 mb-3">
                            <Button
                                variant="primary"
                                size="lg"
                                onClick={abrirDashboardContable}
                                disabled={loading || !clienteId}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                        Preparando dashboard...
                                    </>
                                ) : (
                                    <>
                                        🚀 Ver Dashboard Contable
                                    </>
                                )}
                            </Button>
                        </div>
                        <small className="text-muted">
                            Método POST: Verifica permisos y abre el dashboard
                        </small>
                    </Col>
                    
                    <Col md={6}>
                        <div className="d-grid gap-2 mb-3">
                            <Button
                                variant="outline-primary"
                                size="lg"
                                onClick={abrirDashboardDirecto}
                                disabled={!clienteId}
                            >
                                ⚡ Acceso Directo
                            </Button>
                        </div>
                        <small className="text-muted">
                            Método GET: Redireccionamiento directo
                        </small>
                    </Col>
                </Row>

                <hr />
                
                <div className="text-muted small">
                    <h6>ℹ️ Información técnica:</h6>
                    <ul className="mb-0">
                        <li><strong>Endpoint POST:</strong> <code>/api/dashboard-streamlit/</code></li>
                        <li><strong>Endpoint GET:</strong> <code>/api/dashboard-streamlit/{clienteId}/</code></li>
                        <li><strong>Parámetro Streamlit:</strong> <code>?cliente_id={clienteId}</code></li>
                        <li><strong>Verificación de permisos:</strong> Automática según tipo de usuario</li>
                    </ul>
                </div>
            </Card.Body>
        </Card>
    );
};

export default DashboardStreamlitAccess;
