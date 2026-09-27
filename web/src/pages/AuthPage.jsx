import { useState } from "react";
import CosmicBackground from "@/components/layout/CosmicBackground.jsx";
import { NetworkLogo } from "@/components/icons/index.jsx";
import { login, registerAccount } from "@/lib/api.js";
import "./auth.css";

const EMPTY = {
  firstName: "",
  lastName: "",
  username: "",
  password: "",
  confirm: "",
  phone: "",
  email: "",
};

const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.7,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

function Glyph({ children }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {children}
    </svg>
  );
}

function UserGlyph() {
  return (
    <Glyph>
      <circle cx="12" cy="8" r="3.2" {...stroke} />
      <path d="M5.5 19.2c1.1-3.2 3.4-4.7 6.5-4.7s5.4 1.5 6.5 4.7" {...stroke} />
    </Glyph>
  );
}

function LockGlyph() {
  return (
    <Glyph>
      <rect x="5" y="10.5" width="14" height="9" rx="2" {...stroke} />
      <path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" {...stroke} />
    </Glyph>
  );
}

function MailGlyph() {
  return (
    <Glyph>
      <rect x="3.5" y="5.5" width="17" height="13" rx="2" {...stroke} />
      <path d="M4 7l8 6 8-6" {...stroke} />
    </Glyph>
  );
}

function PhoneGlyph() {
  return (
    <Glyph>
      <path
        d="M8.2 4.8h2.1l1.1 2.6-1.5 1.1a12 12 0 0 0 5.6 5.6l1.1-1.5 2.6 1.1v2.1c0 .7-.6 1.3-1.3 1.3A13.2 13.2 0 0 1 6.9 6.1c0-.7.6-1.3 1.3-1.3Z"
        {...stroke}
      />
    </Glyph>
  );
}

function EyeGlyph({ off }) {
  return (
    <Glyph>
      <path d="M2.8 12S6.2 6.8 12 6.8 21.2 12 21.2 12 17.8 17.2 12 17.2 2.8 12 2.8 12Z" {...stroke} />
      <circle cx="12" cy="12" r="2.4" {...stroke} />
      {off ? <path d="M5 19L19 5" {...stroke} /> : null}
    </Glyph>
  );
}

function TextField({ label, hint, icon, dir, type = "text", ...inputProps }) {
  return (
    <label className="auth-field">
      <span className="auth-label-line">
        {label}
        {hint ? <span className="auth-optional">{hint}</span> : null}
      </span>
      <span className="auth-control">
        {icon}
        <input dir={dir} type={type} {...inputProps} />
      </span>
    </label>
  );
}

function PasswordField({ label, value, onChange, autoComplete, revealed, onToggle }) {
  return (
    <label className="auth-field">
      <span className="auth-label-line">{label}</span>
      <span className="auth-control is-secret">
        <LockGlyph />
        <input
          dir="ltr"
          type={revealed ? "text" : "password"}
          value={value}
          autoComplete={autoComplete}
          onChange={onChange}
        />
        <button
          type="button"
          className="auth-reveal"
          aria-label={revealed ? "پنهان کردن رمز" : "نمایش رمز"}
          aria-pressed={revealed}
          onClick={onToggle}
        >
          <EyeGlyph off={revealed} />
        </button>
      </span>
    </label>
  );
}

export default function AuthPage({ mode, onMode, onSuccess }) {
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [reveal, setReveal] = useState(false);
  const isRegister = mode === "register";

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function switchMode(next) {
    setError("");
    setReveal(false);
    setForm(EMPTY);
    onMode(next);
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (pending) {
      return;
    }
    const username = form.username.trim();
    const password = form.password;
    if (isRegister) {
      const firstName = form.firstName.trim();
      const lastName = form.lastName.trim();
      if (!firstName || !lastName || !username || !password) {
        setError("نام، نام خانوادگی، نام کاربری و رمز لازم است");
        return;
      }
      if (password.length < 8) {
        setError("رمز باید حداقل ۸ نویسه باشد");
        return;
      }
      if (password !== form.confirm) {
        setError("تکرار رمز با رمز یکی نیست");
        return;
      }
    } else if (!username || !password) {
      setError("نام کاربری و رمز را وارد کنید");
      return;
    }

    setPending(true);
    setError("");
    try {
      const payload = isRegister
        ? await registerAccount({
            first_name: form.firstName.trim(),
            last_name: form.lastName.trim(),
            username,
            password,
            ...(form.phone.trim() ? { phone: form.phone.trim() } : {}),
            ...(form.email.trim() ? { email: form.email.trim() } : {}),
          })
        : await login(username, password);
      onSuccess(payload.user);
    } catch (caught) {
      setError(caught.message || "درخواست ناموفق بود");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-screen">
      <CosmicBackground />
      <div className={`auth-stage ${isRegister ? "is-register" : "is-login"}`}>
        <aside className="auth-showcase">
          <div className="auth-logo-wrap">
            <NetworkLogo />
          </div>
          <div className="auth-copy">
            <p className="auth-kicker">پلتفرم سازمانی</p>
            <h1 id="auth-title">سامانه هوشمند مدیریت سازمان</h1>
            <p className="auth-lead">پروژه‌ها، وظایف، جلسات و گزارش‌ها در یک نما.</p>
          </div>
          <ul className="auth-points">
            <li>
              <span>۱</span>
              <div>
                <strong>کار روزانه تیم</strong>
                <em>پروژه، وظیفه و پیگیری</em>
              </div>
            </li>
            <li>
              <span>۲</span>
              <div>
                <strong>جلسه و یادآوری</strong>
                <em>هماهنگی بدون از قلم افتادن</em>
              </div>
            </li>
            <li>
              <span>۳</span>
              <div>
                <strong>تصویر کلی سازمان</strong>
                <em>گزارش، مالی و وضعیت‌ها</em>
              </div>
            </li>
          </ul>
        </aside>

        <section className="auth-panel" aria-labelledby="auth-title">
          <header className="auth-form-head">
            <h2>{isRegister ? "ساخت حساب" : "خوش آمدید"}</h2>
            <p>{isRegister ? "اطلاعات حساب را کامل کنید" : "با حساب سامانه وارد شوید"}</p>
          </header>

          <div className={`auth-tabs ${isRegister ? "is-register" : ""}`} role="tablist" aria-label="ورود یا ثبت‌نام">
            <span className="auth-tab-indicator" aria-hidden="true" />
            <button
              type="button"
              role="tab"
              aria-selected={!isRegister}
              className={!isRegister ? "is-active" : ""}
              onClick={() => switchMode("login")}
            >
              ورود
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={isRegister}
              className={isRegister ? "is-active" : ""}
              onClick={() => switchMode("register")}
            >
              ثبت‌نام
            </button>
          </div>

          <form className="auth-form" onSubmit={onSubmit} noValidate>
            {isRegister ? (
              <div className="auth-row">
                <TextField
                  label="نام"
                  value={form.firstName}
                  autoComplete="given-name"
                  placeholder="نام"
                  onChange={(event) => update("firstName", event.target.value)}
                />
                <TextField
                  label="نام خانوادگی"
                  value={form.lastName}
                  autoComplete="family-name"
                  placeholder="نام خانوادگی"
                  onChange={(event) => update("lastName", event.target.value)}
                />
              </div>
            ) : null}

            <TextField
              label="نام کاربری"
              icon={<UserGlyph />}
              dir="ltr"
              value={form.username}
              autoComplete="username"
              placeholder="username"
              onChange={(event) => update("username", event.target.value)}
            />

            {isRegister ? (
              <div className="auth-row">
                <PasswordField
                  label="رمز"
                  value={form.password}
                  autoComplete="new-password"
                  revealed={reveal}
                  onToggle={() => setReveal((current) => !current)}
                  onChange={(event) => update("password", event.target.value)}
                />
                <PasswordField
                  label="تکرار رمز"
                  value={form.confirm}
                  autoComplete="new-password"
                  revealed={reveal}
                  onToggle={() => setReveal((current) => !current)}
                  onChange={(event) => update("confirm", event.target.value)}
                />
              </div>
            ) : (
              <PasswordField
                label="رمز"
                value={form.password}
                autoComplete="current-password"
                revealed={reveal}
                onToggle={() => setReveal((current) => !current)}
                onChange={(event) => update("password", event.target.value)}
              />
            )}

            {isRegister ? (
              <>
                <div className="auth-row">
                  <TextField
                    label="تلفن"
                    hint="اختیاری"
                    icon={<PhoneGlyph />}
                    dir="ltr"
                    inputMode="tel"
                    value={form.phone}
                    autoComplete="tel"
                    placeholder="09…"
                    onChange={(event) => update("phone", event.target.value)}
                  />
                  <TextField
                    label="ایمیل"
                    hint="اختیاری"
                    icon={<MailGlyph />}
                    dir="ltr"
                    type="email"
                    value={form.email}
                    autoComplete="email"
                    placeholder="name@org.ir"
                    onChange={(event) => update("email", event.target.value)}
                  />
                </div>
                <p className="auth-note">
                  اگر هنوز کاربری در سامانه نباشد، این حساب مدیر کل می‌شود و همهٔ مجوزها را دارد.
                  حساب‌های بعدی با نقش کاربر ساخته می‌شوند.
                </p>
              </>
            ) : null}

            {error ? (
              <p className="auth-error" role="alert">
                {error}
              </p>
            ) : null}

            <button className="auth-submit" type="submit" disabled={pending}>
              {pending ? "در حال ارسال..." : isRegister ? "ساخت حساب" : "ورود به سامانه"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
