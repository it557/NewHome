import { useEffect, useMemo, useRef, useState } from 'react';

const DEFAULT_STATE = {
  texto1: 'Tipo negocio',
  color_texto1: '#ffffff',
  texto2: 'Calle',
  color_texto2: '#000000',
  texto3: 'números m² construidos',
  color_texto3: '#000000',
  texto4: 'REBAJADO',
  color_texto4: '#ffffff',
  rebajado: true,
  habitaciones: 1,
  banos: 1,
  jardin: true,
  garaje: true,
  piscina: true,
  borde_caracteristicas: 'solid',
  color_borde_caracteristicas: '#111111',
  descripcion: '',
  color_descripcion: '#000000',
  precio: '154.900€',
  color_precio: '#b9cdb8',
  energia: 'E',
  escala_imagenes: 0.93,
  imagen1_escala: 1,
  imagen1_offset_x: 0,
  imagen1_offset_y: 0,
  imagen1_modo: 'contain',
  imagen1_custom_ancho: 100,
  imagen1_custom_alto: 100,
  imagen2_escala: 1,
  imagen2_offset_x: 0,
  imagen2_offset_y: 0,
  imagen2_modo: 'contain',
  imagen2_custom_ancho: 100,
  imagen2_custom_alto: 100,
  imagen3_escala: 1,
  imagen3_offset_x: 0,
  imagen3_offset_y: 0,
  imagen3_modo: 'contain',
  imagen3_custom_ancho: 100,
  imagen3_custom_alto: 100,
  imagen4_escala: 1,
  imagen4_offset_x: 0,
  imagen4_offset_y: 0,
  imagen4_modo: 'contain',
  imagen4_custom_ancho: 100,
  imagen4_custom_alto: 100
};

const DESCRIPCION_MAX = 1500;
const LEGAL_TEXT =
  'En cumplimiento del decreto de la Junta de Andalucía 218/2005 del 11 de octubre, se informa al cliente que los gastos notariales, registrales, ITP y otros gastos inherentes a la compraventa no están incluidos en la venta.';

const countWords = (value) => {
  const trimmed = value.trim();
  if (!trimmed) {
    return 0;
  }
  return trimmed.split(/\s+/).length;
};

const normalizeText = (value) => (value || '').replace(/\s+/g, ' ').trim();
const formatSuperscripts = (value) => (value || '').replace(/m\s*\^?\s*2/gi, 'm²');
const IMAGE_MODES = ['contain', 'cover', 'expand', 'custom'];

const normalizeImageMode = (value) => {
  if (typeof value !== 'string') {
    return 'contain';
  }
  const normalized = value.toLowerCase();
  return IMAGE_MODES.includes(normalized) ? normalized : 'contain';
};

const clampScale = (value) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return DEFAULT_STATE.escala_imagenes;
  }
  return Math.min(1, Math.max(0.01, numeric));
};

const clampCustomDimension = (value) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return 100;
  }
  return Math.min(200, Math.max(1, numeric));
};
const clampOffset = (value) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.min(100, Math.max(-100, numeric));
};

const getImageAdjustments = (state, imageKey) => {
  const baseScale = clampScale(state.escala_imagenes);
  const individualScale = clampScale(state[`${imageKey}_escala`]);
  const mode = normalizeImageMode(state[`${imageKey}_modo`]);
  return {
    mode,
    scale: clampScale(baseScale * individualScale),
    offsetX: clampOffset(state[`${imageKey}_offset_x`]),
    offsetY: clampOffset(state[`${imageKey}_offset_y`]),
    customWidth: clampCustomDimension(state[`${imageKey}_custom_ancho`]),
    customHeight: clampCustomDimension(state[`${imageKey}_custom_alto`])
  };
};

const IMAGE_SLOTS = [
  { key: 'imagen1', label: 'Imagen 1' },
  { key: 'imagen2', label: 'Imagen 2' },
  { key: 'imagen3', label: 'Imagen 3' },
  { key: 'imagen4', label: 'Imagen 4' }
];


const Field = ({ label, children, full = false }) => (
  <label className={`field${full ? ' full' : ''}`}>
    <span className="field-label">{label}</span>
    {children}
  </label>
);

const ColorField = ({ label, value, onChange, onBlur }) => (
  <label className="field">
    <span className="field-label">{label}</span>
    <span className="color-field">
      <span className="palette">🎨</span>
      <input type="color" value={value} onChange={onChange} onBlur={onBlur} />
      <span className="color-value">{value}</span>
    </span>
  </label>
);

const Toggle = ({ label, checked, onChange, onBlur }) => (
  <label className="toggle">
    <span>{label}</span>
    <input
      type="checkbox"
      checked={checked}
      onChange={(event) => {
        onChange(event);
        if (onBlur) {
          onBlur();
        }
      }}
    />
    <span className="slider" />
  </label>
);

const FileField = ({ label, field, files, onFileChange, onClear, onBlur, inputKey }) => (
  <label className="file-field">
    <span className="field-label">{label}</span>
    <span className="file-control">
      <span className="file-button">+</span>
      <span className="file-name">{files[field]?.name || 'Sin archivo'}</span>
      {files[field] && (
        <button
          type="button"
          className="file-clear"
          aria-label={`Quitar ${label}`}
          onClick={(event) => {
            event.preventDefault();
            onClear(field);
          }}
        >
          ×
        </button>
      )}
      <input
        key={inputKey}
        type="file"
        accept="image/*"
        onChange={(event) => {
          onFileChange(field)(event);
          if (onBlur) {
            onBlur();
          }
        }}
      />
    </span>
  </label>
);

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [form, setForm] = useState(DEFAULT_STATE);
  const [files, setFiles] = useState({
    imagen1: null,
    imagen2: null,
    imagen3: null,
    imagen4: null,
    qr_imagen: null
  });
  const [fileInputKeys, setFileInputKeys] = useState({
    imagen1: 0,
    imagen2: 0,
    imagen3: 0,
    imagen4: 0,
    qr_imagen: 0
  });
  const [loading, setLoading] = useState(false);
  const [previewImages, setPreviewImages] = useState({
    imagen1: '',
    imagen2: '',
    imagen3: '',
    imagen4: '',
    qr_imagen: ''
  });
  const [descDraft, setDescDraft] = useState('');
  const [drafts, setDrafts] = useState({
    texto1: '',
    texto2: '',
    texto3: '',
    texto4: '',
    precio: '',
    habitaciones: '',
    banos: ''
  });

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 1400);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem('newhome-form');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        const parsedScale = clampScale(parsed?.escala_imagenes);
        setForm((prev) => {
          const next = { ...prev, ...parsed, escala_imagenes: parsedScale };
          IMAGE_SLOTS.forEach(({ key }) => {
            next[`${key}_modo`] = normalizeImageMode(parsed?.[`${key}_modo`]);
            next[`${key}_custom_ancho`] = clampCustomDimension(parsed?.[`${key}_custom_ancho`]);
            next[`${key}_custom_alto`] = clampCustomDimension(parsed?.[`${key}_custom_alto`]);
          });
          return next;
        });
      } catch {
        // ignore
      }
    }
  }, []);

  useEffect(() => {
    setDescDraft(form.descripcion || '');
  }, [form.descripcion]);

  useEffect(() => {
    const nextDrafts = {
      texto1: form.texto1 || '',
      texto2: form.texto2 || '',
      texto3: form.texto3 || '',
      texto4: form.texto4 || '',
      precio: form.precio || '',
      habitaciones: String(form.habitaciones ?? ''),
      banos: String(form.banos ?? '')
    };
    setDrafts((prev) => {
      if (
        prev.texto1 === nextDrafts.texto1 &&
        prev.texto2 === nextDrafts.texto2 &&
        prev.texto3 === nextDrafts.texto3 &&
        prev.texto4 === nextDrafts.texto4 &&
        prev.precio === nextDrafts.precio &&
        prev.habitaciones === nextDrafts.habitaciones &&
        prev.banos === nextDrafts.banos
      ) {
        return prev;
      }
      return nextDrafts;
    });
  }, [
    form.texto1,
    form.texto2,
    form.texto3,
    form.texto4,
    form.precio,
    form.habitaciones,
    form.banos
  ]);

  useEffect(() => {
    const next = {};
    Object.entries(files).forEach(([key, file]) => {
      if (file) {
        next[key] = URL.createObjectURL(file);
      }
    });
    setPreviewImages((prev) => {
      Object.values(prev).forEach((url) => {
        if (url) {
          URL.revokeObjectURL(url);
        }
      });
      return {
        imagen1: next.imagen1 || '',
        imagen2: next.imagen2 || '',
        imagen3: next.imagen3 || '',
        imagen4: next.imagen4 || '',
        qr_imagen: next.qr_imagen || ''
      };
    });
    return () => {
      Object.values(next).forEach((url) => {
        if (url) {
          URL.revokeObjectURL(url);
        }
      });
    };
  }, [files]);

  useEffect(() => {
    localStorage.setItem('newhome-form', JSON.stringify(form));
  }, [form]);

  const logoUrl = useMemo(() => '/static/logo_new_home.png', []);
  const xfuegoUrl = useMemo(() => '/static/XFuego.png', []);

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoginError('');
    const body = new FormData();
    body.append('username', loginForm.username);
    body.append('password', loginForm.password);
    const response = await fetch('/api/login', { method: 'POST', body });
    if (response.ok) {
      setLoggedIn(true);
      return;
    }
    setLoginError('Usuario o contraseña incorrectos');
  };

  const handleChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    if (field === 'escala_imagenes') {
      setForm((prev) => ({ ...prev, escala_imagenes: clampScale(value) }));
      return;
    }
    if (field.endsWith('_escala')) {
      setForm((prev) => ({ ...prev, [field]: clampScale(value) }));
      return;
    }
    if (field.endsWith('_offset_x') || field.endsWith('_offset_y')) {
      setForm((prev) => ({ ...prev, [field]: clampOffset(value) }));
      return;
    }
    if (field.endsWith('_modo')) {
      setForm((prev) => ({ ...prev, [field]: normalizeImageMode(value) }));
      return;
    }
    if (field.endsWith('_custom_ancho') || field.endsWith('_custom_alto')) {
      setForm((prev) => ({ ...prev, [field]: clampCustomDimension(value) }));
      return;
    }
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleFile = (field) => (event) => {
    const file = event.target.files?.[0] || null;
    setFiles((prev) => ({ ...prev, [field]: file }));
  };

  const handleClearFile = (field) => {
    setFiles((prev) => ({ ...prev, [field]: null }));
    setFileInputKeys((prev) => ({ ...prev, [field]: prev[field] + 1 }));
  };

  const buildPayload = (nextForm = form, nextFiles = files) => {
    const body = new FormData();
    Object.entries(nextForm).forEach(([key, value]) => body.append(key, String(value)));
    Object.entries(nextFiles).forEach(([key, file]) => {
      if (file) {
        body.append(key, file);
      }
    });
    return body;
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/pdf', { method: 'POST', body: buildPayload() });
      if (!response.ok) {
        throw new Error('No se pudo generar el PDF');
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'NewHomeGenerator.pdf';
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert(error.message || 'Error al generar el PDF');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {};


  const handleReset = () => {
    setForm(DEFAULT_STATE);
    setFiles({
      imagen1: null,
      imagen2: null,
      imagen3: null,
      imagen4: null,
      qr_imagen: null
    });
    setDescDraft('');
    setDrafts({
      texto1: DEFAULT_STATE.texto1,
      texto2: DEFAULT_STATE.texto2,
      texto3: DEFAULT_STATE.texto3,
      texto4: DEFAULT_STATE.texto4,
      precio: DEFAULT_STATE.precio,
      habitaciones: String(DEFAULT_STATE.habitaciones),
      banos: String(DEFAULT_STATE.banos)
    });
    localStorage.removeItem('newhome-form');
  };

  const updateDraft = (field, parser = (value) => value) => (event) => {
    const value = event.target.value;
    setDrafts((prev) => ({ ...prev, [field]: value }));
    setForm((prev) => ({ ...prev, [field]: parser(value) }));
  };

  const energyLevels = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
  const energyIndex = Math.max(0, energyLevels.indexOf(form.energia || 'E'));
  const baseTop = (energyIndex + 0.5) * (100 / 7);
  const energyOffsets = {
    A: 6.5,
    B: 4.8,
    C: 1.2,
    D: 0,
    E: 0,
    F: -4.2,
    G: -7.8
  };
  const energyTop = `${baseTop + (energyOffsets[energyLevels[energyIndex]] ?? 0)}%`;
  const energyXOffsets = {
    F: 6,
    G: 8,
    D: -2,
    E: -2,
    A: -15,
    B: -10,
    C: 0  
  };
  const energyX = energyXOffsets[energyLevels[energyIndex]] ?? 0;
  const descriptionText = normalizeText(form.descripcion);
  const isLongDescription = descriptionText.length > 1000;
  const borderStyle = form.borde_caracteristicas || 'solid';
  const borderColor = form.color_borde_caracteristicas || '#111111';
  const borderWidth = borderStyle === 'double' ? '3px' : ['groove', 'ridge', 'inset', 'outset'].includes(borderStyle) ? '2px' : '1px';

  if (showSplash) {
    return (
      <div className="splash">
        <img className="xfuego-mark splash-mark" src={xfuegoUrl} alt="XFuego" />
      </div>
    );
  }

  if (!loggedIn) {
    return (
      <div className="login">
        <div className="login-card">
          <img src={logoUrl} alt="NewHome" onError={(e) => (e.currentTarget.style.display = 'none')} />
          <h2>Inicia sesión</h2>
          <form onSubmit={handleLogin}>
            <label>
              Usuario
              <input
                value={loginForm.username}
                onChange={(event) => setLoginForm((prev) => ({ ...prev, username: event.target.value }))}
                placeholder="Usuario"
              />
            </label>
            <label>
              Contraseña
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm((prev) => ({ ...prev, password: event.target.value }))}
                placeholder="Contraseña"
              />
            </label>
            {loginError && <p className="error">{loginError}</p>}
            <button type="submit">Entrar</button>
          </form>
        </div>
      </div>
    );
  }

  const isBusy = loading;

  return (
    <div className="app">
      <img className="xfuego-mark app-mark" src={xfuegoUrl} alt="XFuego" />
      <div className={`top-progress${isBusy ? ' active' : ''}`} />
      <main className="preview">
        <div className="preview-card">
          <h2>Vista previa</h2>
          <div className="preview-sheet">
            <div className="flyer">
              <header className="flyer-header" style={{ backgroundColor: '#213502' }}>
                <div className="flyer-title" style={{ color: form.color_texto1 }}>{(form.texto1 || 'TEXTO 1').toUpperCase()}</div>
                <img className="flyer-logo" src={logoUrl} alt="NewHome" onError={(e) => (e.currentTarget.style.display = 'none')} />
              </header>

              <div className="flyer-subheader">
                <div className="flyer-subtext" style={{ color: form.color_texto2 }}>{form.texto2 || 'TEXTO 2'}</div>
                <div className="flyer-subtext" style={{ color: form.color_texto3 }}>{formatSuperscripts(form.texto3 || 'TEXTO 3')}</div>
              </div>

              <div className="flyer-grid">
                {IMAGE_SLOTS.map(({ key, label }) => {
                  const { mode, scale, offsetX, offsetY, customWidth, customHeight } = getImageAdjustments(form, key);
                  const fitMode = mode === 'expand' || mode === 'custom' ? 'fill' : mode;
                  const renderedWidth = mode === 'custom' ? customWidth : 100;
                  const renderedHeight = mode === 'custom' ? customHeight : 100;
                  return (
                    <div
                      key={key}
                      className="flyer-cell"
                      style={{
                        '--img-fit': fitMode,
                        '--img-width': `${renderedWidth}%`,
                        '--img-height': `${renderedHeight}%`,
                        '--img-scale': String(scale),
                        '--img-offset-x': `${offsetX / 2}%`,
                        '--img-offset-y': `${offsetY / 2}%`
                      }}
                    >
                    {previewImages[key] ? (
                      <img src={previewImages[key]} alt={label} />
                    ) : (
                      <span className="flyer-cell-placeholder">{label}</span>
                    )}
                    </div>
                  );
                })}
                {form.rebajado && (
                  <div className="flyer-band">
                    <span style={{ color: form.color_texto4 }}>{(form.texto4 || 'REBAJADO').toUpperCase()}</span>
                  </div>
                )}
              </div>

              <div
                className="flyer-icons"
                style={{
                  borderStyle,
                  borderColor,
                  borderWidth
                }}
              >
                <div className="flyer-icon"><img src="/static/dormitorio.png" alt="Habitaciones" /><span>{form.habitaciones}</span></div>
                <div className="flyer-icon"><img src="/static/aseo.png" alt="Baños" /><span>{form.banos}</span></div>
                <div className="flyer-icon"><img src="/static/jardin.png" alt="Jardín" /><span className={form.jardin ? 'flag yes' : 'flag no'}>{form.jardin ? '✓' : '✗'}</span></div>
                <div className="flyer-icon"><img src="/static/garaje.png" alt="Garaje" /><span className={form.garaje ? 'flag yes' : 'flag no'}>{form.garaje ? '✓' : '✗'}</span></div>
                <div className="flyer-icon"><img src="/static/piscina.png" alt="Piscina" /><span className={form.piscina ? 'flag yes' : 'flag no'}>{form.piscina ? '✓' : '✗'}</span></div>
              </div>

              <div className="flyer-details">
                <div className="flyer-qr">
                  {previewImages.qr_imagen ? <img src={previewImages.qr_imagen} alt="QR" /> : null}
                </div>
                <p
                  className={`flyer-desc-text${isLongDescription ? ' long' : ''}`}
                  style={{ color: form.color_descripcion }}
                >
                  {descriptionText}
                </p>
                <div className="flyer-energy">
                  <div className="energy-box">
                    <img src="/static/certificado.png" alt="Energía" />
                    <span className="energy-arrow" style={{ top: energyTop, transform: `translateX(${energyX}px)` }} />
                  </div>
                </div>
                <div className="flyer-price-label">Precio</div>
                <div className="flyer-price" style={{ color: form.color_precio }}>{form.precio || '0€'}</div>
                <p className="flyer-desc2">{LEGAL_TEXT}</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <aside className="controls">
        <h2>Controles</h2>

        <section className="section-grid">
          <h3>Textos</h3>
          <Field label="Texto 1"><input value={drafts.texto1} onChange={updateDraft('texto1')} /></Field>
          <ColorField label="Elige el color" value={form.color_texto1} onChange={handleChange('color_texto1')} />
          <Field label="Texto 2"><input value={drafts.texto2} onChange={updateDraft('texto2')} /></Field>
          <ColorField label="Elige el color" value={form.color_texto2} onChange={handleChange('color_texto2')} />
          <Field label="Texto 3"><input value={drafts.texto3} onChange={updateDraft('texto3')} /></Field>
          <ColorField label="Elige el color" value={form.color_texto3} onChange={handleChange('color_texto3')} />
          <Field label="Texto 4"><input value={drafts.texto4} onChange={updateDraft('texto4')} /></Field>
          <ColorField label="Elige el color" value={form.color_texto4} onChange={handleChange('color_texto4')} />
        </section>

        <section className="section-grid">
          <h3>Características</h3>
          <Field label="Habitaciones"><input className="number" type="number" value={drafts.habitaciones} onChange={updateDraft('habitaciones', Number)} /></Field>
          <Field label="Baños"><input className="number" type="number" value={drafts.banos} onChange={updateDraft('banos', Number)} /></Field>
          <Toggle label="Jardín" checked={form.jardin} onChange={handleChange('jardin')} />
          <Toggle label="Garaje" checked={form.garaje} onChange={handleChange('garaje')} />
          <Toggle label="Piscina" checked={form.piscina} onChange={handleChange('piscina')} />
          <Field label="Borde iconos">
            <select value={form.borde_caracteristicas} onChange={handleChange('borde_caracteristicas')}>
              <option value="solid">Continuo</option>
              <option value="dashed">Discontinuo</option>
              <option value="dotted">Punteado</option>
              <option value="double">Doble</option>
              <option value="groove">Surco</option>
              <option value="ridge">Relieve</option>
              <option value="inset">Hundido</option>
              <option value="outset">Saliente</option>
            </select>
          </Field>
          <ColorField label="Color borde" value={form.color_borde_caracteristicas} onChange={handleChange('color_borde_caracteristicas')} />
        </section>

        <section className="section-grid">
          <h3>Descripción</h3>
          <Field label="Descripción" full>
            <textarea
              rows="3"
              value={descDraft}
              maxLength={DESCRIPCION_MAX}
              onChange={(event) => {
                const nextValue = event.target.value;
                setDescDraft(nextValue);
                const nextForm = { ...form, descripcion: nextValue };
                setForm(nextForm);
              }}
            />
            <span className="field-meta">
              {countWords(descDraft)} palabras · {descDraft.length}/{DESCRIPCION_MAX} caracteres
            </span>
          </Field>
          <ColorField label="Color descripción" value={form.color_descripcion} onChange={handleChange('color_descripcion')} />
        </section>

        <section className="section-grid">
          <h3>Imágenes</h3>
          <FileField label="Imagen 1" field="imagen1" files={files} onFileChange={handleFile} onClear={handleClearFile} inputKey={`imagen1-${fileInputKeys.imagen1}`} />
          <FileField label="Imagen 2" field="imagen2" files={files} onFileChange={handleFile} onClear={handleClearFile} inputKey={`imagen2-${fileInputKeys.imagen2}`} />
          <FileField label="Imagen 3" field="imagen3" files={files} onFileChange={handleFile} onClear={handleClearFile} inputKey={`imagen3-${fileInputKeys.imagen3}`} />
          <FileField label="Imagen 4" field="imagen4" files={files} onFileChange={handleFile} onClear={handleClearFile} inputKey={`imagen4-${fileInputKeys.imagen4}`} />
          <FileField label="QR" field="qr_imagen" files={files} onFileChange={handleFile} onClear={handleClearFile} inputKey={`qr-${fileInputKeys.qr_imagen}`} />
          <Field label="Ajuste global" full>
            <div className="range-field">
              <input
                type="range"
                min="0.01"
                max="1"
                step="0.01"
                value={clampScale(form.escala_imagenes)}
                onChange={handleChange('escala_imagenes')}
              />
              <span>{Math.round(clampScale(form.escala_imagenes) * 100)}%</span>
            </div>
          </Field>
          <div className="image-adjust-grid">
            {IMAGE_SLOTS.map(({ key, label }) => (
              <details key={`${key}-editor`} className="image-adjust-card">
                <summary>{label}</summary>
                <div className="image-adjust-body">
                  <label>
                    Ajuste
                    <select
                      value={normalizeImageMode(form[`${key}_modo`])}
                      onChange={handleChange(`${key}_modo`)}
                    >
                      <option value="contain">Contain (completa)</option>
                      <option value="cover">Cubrir</option>
                      <option value="expand">Expandir</option>
                      <option value="custom">Personalizar</option>
                    </select>
                  </label>
                  {normalizeImageMode(form[`${key}_modo`]) === 'custom' && (
                    <>
                      <label>
                        Ancho
                        <div className="range-field">
                          <input
                            type="range"
                            min="1"
                            max="200"
                            step="1"
                            value={clampCustomDimension(form[`${key}_custom_ancho`])}
                            onChange={handleChange(`${key}_custom_ancho`)}
                          />
                          <span>{Math.round(clampCustomDimension(form[`${key}_custom_ancho`]))}%</span>
                        </div>
                      </label>
                      <label>
                        Alto
                        <div className="range-field">
                          <input
                            type="range"
                            min="1"
                            max="200"
                            step="1"
                            value={clampCustomDimension(form[`${key}_custom_alto`])}
                            onChange={handleChange(`${key}_custom_alto`)}
                          />
                          <span>{Math.round(clampCustomDimension(form[`${key}_custom_alto`]))}%</span>
                        </div>
                      </label>
                    </>
                  )}
                  <label>
                    Zoom
                    <div className="range-field">
                      <input
                        type="range"
                        min="0.01"
                        max="1"
                        step="0.01"
                        value={clampScale(form[`${key}_escala`])}
                        onChange={handleChange(`${key}_escala`)}
                      />
                      <span>{Math.round(clampScale(form[`${key}_escala`]) * 100)}%</span>
                    </div>
                  </label>
                  <label>
                    Horizontal
                    <div className="range-field">
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        step="1"
                        value={clampOffset(form[`${key}_offset_x`])}
                        onChange={handleChange(`${key}_offset_x`)}
                      />
                      <span>{clampOffset(form[`${key}_offset_x`])}</span>
                    </div>
                  </label>
                  <label>
                    Vertical
                    <div className="range-field">
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        step="1"
                        value={clampOffset(form[`${key}_offset_y`])}
                        onChange={handleChange(`${key}_offset_y`)}
                      />
                      <span>{clampOffset(form[`${key}_offset_y`])}</span>
                    </div>
                  </label>
                </div>
              </details>
            ))}
          </div>
        </section>

        <section className="section-grid">
          <h3>Extras</h3>
          <Field label="Precio"><input value={drafts.precio} onChange={updateDraft('precio')} /></Field>
          <ColorField label="Color Precio" value={form.color_precio} onChange={handleChange('color_precio')} />
          <Field label="Energía">
            <select value={form.energia} onChange={handleChange('energia')}>
              {['A', 'B', 'C', 'D', 'E', 'F', 'G'].map((lvl) => (
                <option key={lvl} value={lvl}>{lvl}</option>
              ))}
            </select>
          </Field>
          <Toggle label="Rebajado" checked={form.rebajado} onChange={handleChange('rebajado')} />
        </section>

        <div className="actions">
          <button className="primary" disabled={loading} onClick={handleGenerate}>
            {loading ? 'Generando...' : 'Generar PDF'}
          </button>
          <button className="ghost" type="button" onClick={handleReset}>
            Reiniciar
          </button>
        </div>
      </aside>
    </div>
  );
}
