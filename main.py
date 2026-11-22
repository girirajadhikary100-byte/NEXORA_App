import os, csv, ssl, json, time, random, smtplib, webbrowser, urllib.request
from email.message import EmailMessage
from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform, get_color_from_hex
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image as KivyImage
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

if platform not in ("android", "ios"):
    Window.size = (400, 750)

try:
    from plyer import filechooser
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False

BIO = "Name: Giriraj Adhikary\nRole: Founder & Creator of NEXORA\nDepartment: Electrical Engineering (EE)\nMission: Learn • Practice • Grow — Empowering engineering students with organized Syllabus, Notes, and Previous Year Question Papers."

DEFAULT_EE_SUBS = {
    "1st Semester": [["Mathematics-I", "26-BS-M101", "1100001"], ["Chemistry", "26-BS-CH101", "1100003"], ["Basic Electrical & Electronics Engg", "26-ES-EE101", "1100004"], ["English for Communication Skills", "26-AEC-101", "1100005"]],
    "2nd Semester": [["Mathematics-II", "26-BS-M201", "2100001"], ["Biology for Engineers", "26-BS-BI201", "2100002"], ["Physics", "26-BS-PH201", "2100003"], ["Programming for Problem Solving & AI", "26-ES-CS201", "2100005"], ["Environmental Science", "26-VAC-201", "2100006"]],
    "3rd Semester": [["Electric Circuit Theory", "PC-EE301", "003519"], ["Electro Magnetic Field Theory", "PC-EE303", "003521"], ["Analog Electronics", "PC-EE302", "003520"], ["Engineering Mechanics", "ES-ME301", "003522"], ["Mathematics", "MS-M301", "003523"], ["Biology for Engineers", "BS-EE301", "003524"], ["Indian Constitution", "MC-EE301", "003525"]],
}

def normalize_url(u):
    u = u.strip()
    if "://google.com" in u and "/d/" in u:
        fid = u.split("/d/")[-1].split("/")[0]
        return f"https://://google.com/uc?export=download&id={fid}"
    if "dropbox.com" in u and "dl=0" in u:
        return u.replace("dl=0", "dl=1")
    return u

def show_alert(title, msg):
    box = BoxLayout(orientation="vertical", padding=14, spacing=10)
    lbl = Label(text=msg, color=(1, 1, 1, 1), halign="center", valign="middle")
    lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
    btn = Button(text="OK", size_hint_y=None, height=44, background_normal="", background_color=get_color_from_hex("#FF0000"), bold=True)
    box.add_widget(lbl)
    box.add_widget(btn)
    pop = Popup(title=title, content=box, size_hint=(0.86, 0.42))
    btn.bind(on_release=pop.dismiss)
    pop.open()

def show_confirm(title, msg, on_yes):
    box = BoxLayout(orientation="vertical", padding=14, spacing=10)
    lbl = Label(text=msg, color=(1, 1, 1, 1), halign="center", valign="middle")
    lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
    row = BoxLayout(size_hint_y=None, height=44, spacing=10)
    yes_btn = Button(text="YES", background_normal="", background_color=get_color_from_hex("#FF0000"), bold=True)
    no_btn = Button(text="NO", background_normal="", background_color=get_color_from_hex("#333333"), bold=True)
    row.add_widget(yes_btn)
    row.add_widget(no_btn)
    box.add_widget(lbl)
    box.add_widget(row)
    pop = Popup(title=title, content=box, size_hint=(0.86, 0.4))
    yes_btn.bind(on_release=lambda *a: (pop.dismiss(), on_yes()))
    no_btn.bind(on_release=pop.dismiss)
    pop.open()

def make_btn(text, bg="#FF0000", fg="#FFFFFF", height=48, font_size="14sp", cb=None):
    b = Button(text=text, size_hint_y=None, height=height, background_normal="", background_color=get_color_from_hex(bg), color=get_color_from_hex(fg), bold=True, font_size=font_size, halign="center")
    b.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0] - 16, None)))
    if cb:
        b.bind(on_release=cb)
    return b

def make_input(hint="", text="", password=False, height=44):
    return TextInput(hint_text=hint, text=text, password=password, multiline=False, size_hint_y=None, height=height, background_normal="", background_color=get_color_from_hex("#f2f2f2"), foreground_color=(0, 0, 0, 1), padding=[10, 8], font_size="14sp")

def make_label(text, fg="#111111", font_size="14sp", bold=True, halign="center", height=None):
    lbl = Label(text=text, color=get_color_from_hex(fg), font_size=font_size, bold=bold, halign=halign, valign="middle", size_hint_y=None if height else 1, height=height if height else 30)
    lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)), texture_size=lambda inst, val: setattr(inst, "height", val[1] + 8) if height is None else None)
    return lbl

class BaseScreen(Screen):
    def set_bg_color(self, hex_color="#FFFFFF"):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*get_color_from_hex(hex_color))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda inst, val: setattr(self.bg_rect, "pos", val), size=lambda inst, val: setattr(self.bg_rect, "size", val))

    def build_scroll_page(self, bg_hex="#FFFFFF"):
        self.clear_widgets()
        self.set_bg_color(bg_hex)
        sv = ScrollView(size_hint=(1, 1))
        box = BoxLayout(orientation="vertical", padding=[14, 14], spacing=10, size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        sv.add_widget(box)
        self.add_widget(sv)
        return box

    def add_top_nav(self, container, back_cb, back_txt="<- Back"):
        app = App.get_running_app()
        nav = BoxLayout(size_hint_y=None, height=42, spacing=10)
        nav.add_widget(make_btn(back_txt, "#e6e6e6", "#111111", 40, "13sp", lambda *a: back_cb()))
        nav.add_widget(make_btn("Logout", "#FF0000", "#FFFFFF", 40, "13sp", lambda *a: app.go("home")))
        container.add_widget(nav)

class SplashScreen(BaseScreen):
    def on_enter(self):
        self.clear_widgets()
        self.set_bg_color("#f4f7ff")
        app = App.get_running_app()
        root_box = BoxLayout(orientation="vertical", padding=20, spacing=12)
        bg_path = app.db.get("bg", "")
        if bg_path and os.path.exists(bg_path):
            root_box.add_widget(KivyImage(source=bg_path, allow_stretch=True, keep_ratio=True))
        elif os.path.exists("logo.png"):
            root_box.add_widget(KivyImage(source="logo.png", allow_stretch=True, keep_ratio=True))
        else:
            root_box.add_widget(make_label("NEXORA", "#0b133b", "38sp", True, "center"))
            root_box.add_widget(make_label("Learn  •  Practice  •  Grow", "#3b52b5", "16sp", True, "center"))
        banner = BoxLayout(orientation="vertical", size_hint_y=None, height=140, padding=12, spacing=6)
        with banner.canvas.before:
            Color(*get_color_from_hex("#0b133b"))
            rect = Rectangle(pos=banner.pos, size=banner.size)
        banner.bind(pos=lambda i, v: setattr(rect, "pos", v), size=lambda i, v: setattr(rect, "size", v))
        self.t0 = make_label("", "#00d4ff", "18sp", True, "center", 32)
        self.t1 = make_label("", "#FFFFFF", "14sp", True, "center", 28)
        self.t2 = make_label("", "#00d4ff", "11sp", True, "center", 26)
        banner.add_widget(self.t0)
        banner.add_widget(self.t1)
        banner.add_widget(self.t2)
        root_box.add_widget(banner)
        self.add_widget(root_box)
        self.l0 = "WELCOME TO NEXORA"
        self.l1 = "FOUNDER: GIRIRAJ ADHIKARY"
        self.l2 = "(ELECTRICAL ENGINEERING DEPARTMENT)"
        Clock.schedule_once(lambda dt: self.anim0(0), 0.3)

    def anim0(self, k):
        if k <= len(self.l0):
            self.t0.text = self.l0[:k]
            Clock.schedule_once(lambda dt: self.anim0(k + 1), 0.04)
        else:
            Clock.schedule_once(lambda dt: self.anim1(0), 0.25)

    def anim1(self, i):
        if i <= len(self.l1):
            self.t1.text = self.l1[:i]
            Clock.schedule_once(lambda dt: self.anim1(i + 1), 0.035)
        else:
            Clock.schedule_once(lambda dt: self.anim2(0), 0.15)

    def anim2(self, j):
        if j <= len(self.l2):
            self.t2.text = self.l2[:j]
            Clock.schedule_once(lambda dt: self.anim2(j + 1), 0.03)
        else:
            Clock.schedule_once(lambda dt: App.get_running_app().go("home"), 1.3)

class HomeScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        app.st.update({"role": "", "user": ""})
        box = self.build_scroll_page("#f4f7ff")
        top_bar = BoxLayout(size_hint_y=None, height=42, spacing=10)
        top_bar.add_widget(make_btn("CHANGE BG", "#FF0000", "#FFFFFF", 40, "12sp", lambda *a: app.open_media("bg")))
        top_bar.add_widget(make_btn("KNOW THE FOUNDER", "#0b133b", "#00d4ff", 40, "12sp", lambda *a: app.go("founder")))
        box.add_widget(top_bar)
        bg_path = app.db.get("bg", "")
        if bg_path and os.path.exists(bg_path):
            box.add_widget(KivyImage(source=bg_path, size_hint_y=None, height=200, allow_stretch=True, keep_ratio=True))
        elif os.path.exists("logo.png"):
            box.add_widget(KivyImage(source="logo.png", size_hint_y=None, height=160, allow_stretch=True, keep_ratio=True))
        else:
            box.add_widget(make_label("NEXORA", "#0b133b", "34sp", True, "center", 55))
            box.add_widget(make_label("Learn  •  Practice  •  Grow", "#3b52b5", "14sp", True, "center", 30))
        box.add_widget(make_label("PORTAL ACCESS", "#FF0000", "18sp", True, "center", 40))
        box.add_widget(make_btn("ADMIN SECTION", "#FF0000", "#FFFFFF", 52, "15sp", lambda *a: app.go("admin_gate")))
        box.add_widget(make_btn("STUDENT LOGIN", "#141414", "#FFFFFF", 52, "15sp", lambda *a: app.open_auth("STUDENT")))
        box.add_widget(make_btn("NEW STUDENT REGISTER", "#0b133b", "#00d4ff", 52, "15sp", lambda *a: app.open_auth("REGISTER")))

class AdminGateScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_label("ADMIN SECURITY LOCK", "#FF0000", "18sp", True, "center", 45))
        box.add_widget(make_label("Enter Secret Admin Passcode:", "#333333", "13sp", True, "left", 28))
        gp = make_input("Admin Passcode", password=True)
        box.add_widget(gp)
        box.add_widget(make_btn("UNLOCK ADMIN", "#FF0000", "#FFFFFF", 50, "15sp", lambda *a: self.verify(gp.text)))
        box.add_widget(make_btn("<- Back", "#222222", "#FFFFFF", 44, "14sp", lambda *a: app.go("home")))

    def verify(self, code):
        app = App.get_running_app()
        if code.strip() == app.admin_db.get("gate", "GIRIRAJ2026"):
            app.go("admin_reg") if not app.admin_db.get("registered", False) else app.open_auth("ADMIN")
        else:
            show_alert("Access Denied", "Wrong Admin Passcode!")

class AdminRegisterScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        if app.admin_db.get("registered", False):
            app.open_auth("ADMIN")
            return
        prof = app.admin_db.setdefault("profile", {})
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_label("FOUNDER / ADMIN REGISTRATION", "#FF0000", "16sp", True, "center", 36))
        fields = [("Admin Username *", "username", prof.get("username", "giriraj"), False), ("Admin Password *", "password", "", True), ("Full Name *", "name", prof.get("name", "Giriraj Adhikary"), False), ("Role / Title *", "role", prof.get("role", "Founder & Creator of NEXORA"), False), ("Department *", "dept", prof.get("dept", "Electrical Engineering (EE)"), False), ("College / Institution *", "college", prof.get("college", ""), False), ("Mobile Number *", "mobile", prof.get("mobile", ""), False), ("Email ID *", "email", prof.get("email", "girirajadhikary100@gmail.com"), False)]
        entries = {}
        for lbl, key, val, is_pw in fields:
            box.add_widget(make_label(lbl, "#111111", "12sp", True, "left", 22))
            inp = make_input(lbl, val, is_pw, 42)
            box.add_widget(inp)
            entries[key] = inp
        box.add_widget(make_btn("COMPLETE ADMIN REGISTRATION", "#FF0000", "#FFFFFF", 50, "14sp", lambda *a: self.save_reg(entries)))
        box.add_widget(make_btn("<- Back to Home", "#e6e6e6", "#111111", 42, "13sp", lambda *a: app.go("home")))

    def save_reg(self, entries):
        app = App.get_running_app()
        vals = {k: e.text.strip() for k, e in entries.items()}
        if any(not v for v in vals.values()):
            show_alert("Mandatory (*)", "All fields marked with * are mandatory!")
            return
        if not vals["mobile"].isdigit() or len(vals["mobile"]) < 10:
            show_alert("Invalid Mobile", "Enter valid 10-digit Mobile!")
            return
        if "@" not in vals["email"] or "." not in vals["email"]:
            show_alert("Invalid Email", "Enter valid Email ID!")
            return
        un, pw = vals["username"].lower(), vals["password"]
        app.admin_db["credentials"] = {un: pw}
        app.admin_db["registered"] = True
        app.admin_db["profile"] = {"username": un, "name": vals["name"], "role": vals["role"], "dept": vals["dept"], "college": vals["college"], "mobile": vals["mobile"], "email": vals["email"], "pfp": app.db.get("pfp", "")}
        app.save_admin_db()
        app.db["bio"] = f"Name: {vals['name']}\nRole: {vals['role']}\nDepartment: {vals['dept']}\nCollege: {vals['college']}\nEmail: {vals['email']}\nMission: Learn • Practice • Grow"
        app.save_db()
        app.st.update({"role": "ADMIN", "user": un})
        show_alert("Admin Registered", f"Welcome to NEXORA, {vals['name']}!")
        app.go("admin_profile")

class AuthScreen(BaseScreen):
    role = "STUDENT"
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_btn("KNOW THE FOUNDER", "#0b133b", "#00d4ff", 44, "13sp", lambda *a: app.go("founder")))
        titles = {"ADMIN": "ADMIN LOGIN", "STUDENT": "STUDENT LOGIN", "REGISTER": "NEW STUDENT REGISTER"}
        box.add_widget(make_label(titles[self.role], "#FF0000", "18sp", True, "center", 42))
        box.add_widget(make_label("Username:", "#333333", "13sp", True, "left", 24))
        u = make_input("Enter Username")
        box.add_widget(u)
        box.add_widget(make_label("Password:", "#333333", "13sp", True, "left", 24))
        p = make_input("Enter Password", password=True)
        box.add_widget(p)
        if self.role == "REGISTER":
            box.add_widget(make_label("Confirm Password:", "#333333", "13sp", True, "left", 24))
            cp = make_input("Confirm Password", password=True)
            box.add_widget(cp)
            box.add_widget(make_btn("CREATE ACCOUNT", "#0b133b", "#00d4ff", 50, "15sp", lambda *a: self.signup(u.text, p.text, cp.text)))
        else:
            box.add_widget(make_btn("LOGIN", "#FF0000", "#FFFFFF", 50, "15sp", lambda *a: self.login(u.text, p.text)))
            if self.role == "STUDENT":
                box.add_widget(make_btn("Forgot Username / Password?", "#FFFFFF", "#0b133b", 38, "12sp", lambda *a: app.go("forgot")))
        box.add_widget(make_btn("<- Back", "#222222", "#FFFFFF", 44, "14sp", lambda *a: app.go("home")))

    def login(self, uv, pv):
        app = App.get_running_app()
        un, pw = uv.strip().lower(), pv.strip()
        if self.role == "ADMIN":
            if un and app.admin_db.get("credentials", {}).get(un) == pw:
                app.st.update({"role": "ADMIN", "user": un})
                app.go("depts")
            else:
                show_alert("Error", "Invalid Admin Username or Password!")
            return
        rec = app.db.setdefault("students_db", {}).get(un)
        saved_pw = rec.get("password") if isinstance(rec, dict) else app.db.get("students", {}).get(un)
        if un and saved_pw is not None and saved_pw == pw:
            app.st.update({"role": "STUDENT", "user": un})
            if not isinstance(rec, dict) or not rec.get("name") or not rec.get("email"):
                app.open_stu_profile_edit(un, first_time=True)
            else:
                app.go("depts")
        else:
            show_alert("Login Failed", "Invalid Username or Password!")

    def signup(self, uv, pv, cpv):
        app = App.get_running_app()
        un, pw, cpw = uv.strip().lower(), pv.strip(), cpv.strip()
        if not un or not pw or pw != cpw:
            show_alert("Error", "Check Username/Password!")
            return
        if un in app.admin_db.get("credentials", {}) or un in app.db.setdefault("students_db", {}):
            show_alert("Error", "Username already exists!")
            return
        app.db["students_db"][un] = {"username": un, "password": pw, "name": "", "dept": "", "college": "", "mobile": "", "email": "", "pfp": ""}
        app.save_db()
        app.st.update({"role": "STUDENT", "user": un})
        show_alert("Account Created", "Complete your mandatory (*) profile.")
        app.open_stu_profile_edit(un, first_time=True)

class ForgotScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_btn("<- Back to Login", "#e6e6e6", "#111111", 40, "13sp", lambda *a: app.open_auth("STUDENT")))
        box.add_widget(make_label("ACCOUNT & PASSWORD RECOVERY", "#FF0000", "17sp", True, "center", 42))
        em = make_input("example@gmail.com")
        box.add_widget(em)
        box.add_widget(make_btn("SEND OTP TO EMAIL", "#FF0000", "#FFFFFF", 50, "14sp", lambda *a: self.send_otp(em.text)))

    def send_otp(self, email_in):
        app = App.get_running_app()
        target = email_in.strip().lower()
        matched_user = next((u for u, rec in app.db.setdefault("students_db", {}).items() if rec.get("email", "").strip().lower() == target), None)
        if not matched_user:
            show_alert("Not Found", "No student account registered with this Email ID!")
            return
        otp = str(random.randint(100000, 999999))
        app.st.update({"otp_code": otp, "otp_user": matched_user, "otp_exp": time.time() + 600})
        sender_mail = (app.admin_db.get("smtp", {}).get("email") or "girirajadhikary100@gmail.com").strip()
        ok, err = app.send_sys_email(target, "NEXORA Account Recovery OTP", f"Your NEXORA OTP is: {otp}\nUsername: {matched_user}")
        show_alert("OTP Sent" if ok else "Demo OTP", f"OTP sent to {target}" if ok else f"Demo OTP: {otp} ({err})")
        app.open_verify_otp(target, sender_mail)

class VerifyOtpScreen(BaseScreen):
    target_email = ""
    sender_mail = "girirajadhikary100@gmail.com"
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_btn("<- Change Email", "#e6e6e6", "#111111", 40, "13sp", lambda *a: app.go("forgot")))
        box.add_widget(make_label("ENTER OTP & RECOVER", "#FF0000", "17sp", True, "center", 38))
        oe = make_input("6-Digit OTP")
        np = make_input("New Password", password=True)
        cp = make_input("Confirm Password", password=True)
        box.add_widget(oe); box.add_widget(np); box.add_widget(cp)
        box.add_widget(make_btn("VERIFY OTP & RECOVER", "#FF0000", "#FFFFFF", 50, "14sp", lambda *a: self.reset_pw(oe.text, np.text, cp.text)))

    def reset_pw(self, otp_in, new_pw, conf_pw):
        app = App.get_running_app()
        if time.time() > app.st.get("otp_exp", 0) or otp_in.strip() != app.st.get("otp_code"):
            show_alert("Error", "Invalid or Expired OTP!")
            return
        if not new_pw.strip() or new_pw.strip() != conf_pw.strip():
            show_alert("Error", "Passwords do not match!")
            return
        un = app.st.get("otp_user", "")
        if un in app.db.setdefault("students_db", {}):
            app.db["students_db"][un]["password"] = new_pw.strip()
            app.save_db()
            show_alert("Recovered!", f"Username: {un}\nPassword updated!")
            app.open_auth("STUDENT")

class FounderScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_btn("<- Back", "#e6e6e6", "#111111", 40, "13sp", lambda *a: app.go("depts" if app.st.get("role") in ("ADMIN", "STUDENT") else "home")))
        box.add_widget(make_label("KNOW THE FOUNDER", "#FF0000", "18sp", True, "center", 38))
        pfp_src = app.admin_db.get("profile", {}).get("pfp") or app.db.get("pfp") or app.db.get("bg")
        if pfp_src and os.path.exists(pfp_src):
            box.add_widget(KivyImage(source=pfp_src, size_hint_y=None, height=160, allow_stretch=True, keep_ratio=True))
            box.add_widget(make_btn("Tap to Enlarge Photo", "#f2f4f8", "#0b133b", 36, "12sp", lambda *a: app.enlarge_photo(pfp_src, "GIRIRAJ ADHIKARY")))
        box.add_widget(make_label(app.db.get("bio", BIO), "#111111", "13sp", False, "left"))
        if app.st.get("role") == "ADMIN":
            row = BoxLayout(size_hint_y=None, height=46, spacing=8)
            row.add_widget(make_btn("Change Photo", "#FF0000", "#FFFFFF", 44, "12sp", lambda *a: app.open_media("pfp")))
            row.add_widget(make_btn("Edit Bio", "#141414", "#FFFFFF", 44, "12sp", lambda *a: app.go("edit_bio")))
            box.add_widget(row)

class EditBioScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_label("EDIT FOUNDER BIO", "#FF0000", "17sp", True, "center", 40))
        ti = TextInput(text=app.db.get("bio", BIO), size_hint_y=None, height=200, background_normal="", background_color=get_color_from_hex("#f2f2f2"), foreground_color=(0, 0, 0, 1))
        box.add_widget(ti)
        box.add_widget(make_btn("SAVE BIO", "#FF0000", "#FFFFFF", 48, "14sp", lambda *a: (app.db.update({"bio": ti.text.strip()}), app.save_db(), app.go("founder"))))
        box.add_widget(make_btn("Cancel", "#e6e6e6", "#111111", 42, "13sp", lambda *a: app.go("founder")))

class MediaScreen(BaseScreen):
    key = "bg"
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_label("SET PHOTO / BACKGROUND", "#FF0000", "17sp", True, "center", 40))
        k_inp = make_input("Admin Master Key", password=True)
        if self.key == "bg" and app.st.get("role") != "ADMIN":
            box.add_widget(k_inp)
        box.add_widget(make_btn("+ Pick Offline Image", "#FF0000", "#FFFFFF", 48, "14sp", lambda *a: self.pick_offline(k_inp.text)))
        u_inp = make_input("https://", "https://")
        box.add_widget(u_inp)
        box.add_widget(make_btn("Set Online Image URL", "#b30000", "#FFFFFF", 48, "14sp", lambda *a: self.download_img(k_inp.text, u_inp.text)))
        box.add_widget(make_btn("Back", "#e6e6e6", "#111111", 42, "13sp", lambda *a: app.go("founder" if self.key == "pfp" else "home")))

    def pick_offline(self, kv):
        app = App.get_running_app()
        if app.st.get("role") != "ADMIN" and kv.strip() != app.admin_db.get("gate", "GIRIRAJ2026"):
            show_alert("Denied", "Admin Access Required!"); return
        if not HAS_PLYER:
            show_alert("Info", "Use Online Image URL."); return
        filechooser.open_file(on_selection=lambda sel: self._save_img(open(sel[0], "rb").read(), os.path.splitext(sel[0])[1] or ".png") if sel else None)

    def download_img(self, kv, url):
        app = App.get_running_app()
        if app.st.get("role") != "ADMIN" and kv.strip() != app.admin_db.get("gate", "GIRIRAJ2026"):
            show_alert("Denied", "Admin Access Required!"); return
        try:
            u = normalize_url(url)
            raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read()
            self._save_img(raw, os.path.splitext(u.split("?")[0])[1] or ".png")
        except Exception as e:
            show_alert("Error", str(e))

    def _save_img(self, raw, ext):
        app = App.get_running_app()
        dest = os.path.join(app.base_dir, f"{self.key}_{int(time.time())}{ext}")
        open(dest, "wb").write(raw)
        app.db[self.key] = dest; app.save_db()
        if self.key == "pfp":
            app.admin_db.setdefault("profile", {})["pfp"] = dest; app.save_admin_db(); app.go("founder")
        else:
            app.go("home")

class StudentProfileScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        un = app.st.get("user", "")
        prof = app.db.setdefault("students_db", {}).get(un, {})
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_btn("<- Back to Departments", "#e6e6e6", "#111111", 40, "13sp", lambda *a: app.go("depts")))
        box.add_widget(make_label("MY STUDENT PROFILE", "#FF0000", "17sp", True, "center", 36))
        if prof.get("pfp") and os.path.exists(prof["pfp"]):
            box.add_widget(KivyImage(source=prof["pfp"], size_hint_y=None, height=140, allow_stretch=True, keep_ratio=True))
        box.add_widget(make_label(f"Username: {un}\nName: {prof.get('name', '-')}\nDept: {prof.get('dept', '-')}\nCollege: {prof.get('college', '-')}\nMobile: {prof.get('mobile', '-')}\nEmail: {prof.get('email', '-')}", "#111111", "13sp", True, "left"))
        box.add_widget(make_btn("Edit Info", "#141414", "#FFFFFF", 44, "12sp", lambda *a: app.open_stu_profile_edit(un, False)))

class StudentEditProfileScreen(BaseScreen):
    un = ""; first_time = True
    def on_enter(self):
        app = App.get_running_app()
        existing = app.db.setdefault("students_db", {}).get(self.un, {})
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_label("STUDENT PROFILE (* MANDATORY)", "#FF0000", "16sp", True, "center", 36))
        entries = {}
        for lbl, key in [("Full Name *", "name"), ("Department *", "dept"), ("College Name *", "college"), ("Mobile Number *", "mobile"), ("Email ID *", "email")]:
            box.add_widget(make_label(lbl, "#111111", "12sp", True, "left", 22))
            inp = make_input(lbl, existing.get(key, ""), False, 42)
            box.add_widget(inp); entries[key] = inp
        box.add_widget(make_btn("SAVE PROFILE", "#FF0000", "#FFFFFF", 50, "14sp", lambda *a: self.save_prof(entries)))
        box.add_widget(make_btn("<- Back", "#e6e6e6", "#111111", 42, "13sp", lambda *a: app.go("home" if self.first_time else "stu_profile")))

    def save_prof(self, entries):
        app = App.get_running_app()
        vals = {k: e.text.strip() for k, e in entries.items()}
        if any(not v for v in vals.values()) or not vals["mobile"].isdigit() or "@" not in vals["email"]:
            show_alert("Invalid Input", "Fill all * fields properly!"); return
        app.db.setdefault("students_db", {}).setdefault(self.un, {"username": self.un}).update(vals)
        app.save_db()
        if self.first_time:
            app.send_sys_email(vals["email"], "Welcome to NEXORA", f"Welcome to NEXORA, {vals['name']}!")
            show_alert("Registered", "Welcome to NEXORA!"); app.open_auth("STUDENT")
        else:
            show_alert("Updated", "Profile updated!"); app.go("stu_profile")

class AdminProfileScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        prof = app.admin_db.setdefault("profile", {})
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_btn("<- Back to Dashboard", "#e6e6e6", "#111111", 40, "13sp", lambda *a: app.go("depts")))
        box.add_widget(make_label("FOUNDER / ADMIN PROFILE", "#FF0000", "17sp", True, "center", 36))
        pfp_path = prof.get("pfp") or app.db.get("pfp", "")
        if pfp_path and os.path.exists(pfp_path):
            box.add_widget(KivyImage(source=pfp_path, size_hint_y=None, height=140, allow_stretch=True, keep_ratio=True))
        box.add_widget(make_label(f"Username: {prof.get('username', '-')}\nName: {prof.get('name', '-')}\nRole: {prof.get('role', '-')}\nDept: {prof.get('dept', '-')}\nCollege: {prof.get('college', '-')}\nMobile: {prof.get('mobile', '-')}\nEmail: {prof.get('email', '-')}", "#111111", "13sp", True, "left"))
        box.add_widget(make_btn("Change Profile Photo", "#FF0000", "#FFFFFF", 46, "13sp", lambda *a: app.open_media("pfp")))

class ManageStudentsScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        all_stu = app.db.setdefault("students_db", {})
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_label(f"STUDENTS ({len(all_stu)} REGISTERED)", "#FF0000", "16sp", True, "center", 36))
        box.add_widget(make_btn("EXPORT TO CSV", "#0b133b", "#00d4ff", 44, "13sp", lambda *a: self.export_csv()))
        for u, rec in list(all_stu.items()):
            box.add_widget(make_label(f"User: {u} | {rec.get('name') or '-'} | {rec.get('mobile') or '-'}", "#111111", "12sp", True, "left", 32))
            box.add_widget(make_btn("Delete Student", "#FF0000", "#FFFFFF", 34, "12sp", lambda *a, x=u: (app.db["students_db"].pop(x, None), app.save_db(), self.on_enter())))
        box.add_widget(make_btn("<- Back", "#e6e6e6", "#111111", 44, "14sp", lambda *a: app.go("depts")))

    def export_csv(self):
        app = App.get_running_app()
        all_stu = app.db.setdefault("students_db", {})
        path = os.path.join(app.base_dir, f"NEXORA_Students_{time.strftime('%Y%m%d_%H%M%S')}.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f); w.writerow(["Username", "Password", "Name", "Dept", "College", "Mobile", "Email"])
            for u, r in all_stu.items(): w.writerow([u, r.get("password",""), r.get("name",""), r.get("dept",""), r.get("college",""), r.get("mobile",""), r.get("email","")])
        show_alert("Exported", f"Saved to:\n{path}")

class ChangePasscodeScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        smtp_cfg = app.admin_db.setdefault("smtp", {"email": "girirajadhikary100@gmail.com", "app_pass": ""})
        adm_un = app.st.get("user") or "giriraj"
        box = self.build_scroll_page("#FFFFFF")
        box.add_widget(make_label("ADMIN SECURITY & AUTO EMAIL", "#FF0000", "16sp", True, "center", 36))
        ng = make_input("Gate Passcode", app.admin_db.get("gate", "GIRIRAJ2026"), False, 42)
        np = make_input("Admin Password", app.admin_db.get("credentials", {}).get(adm_un, "1234"), False, 42)
        se = make_input("Sender Gmail", smtp_cfg.get("email", "girirajadhikary100@gmail.com"), False, 42)
        sp = make_input("16-Digit App Password", smtp_cfg.get("app_pass", ""), True, 42)
        for w in (ng, np, se, sp): box.add_widget(w)
        box.add_widget(make_btn("SAVE TO ADMIN DB", "#FF0000", "#FFFFFF", 48, "14sp", lambda *a: self.save_sec(adm_un, ng.text, np.text, se.text, sp.text)))
        box.add_widget(make_btn("<- Back", "#e6e6e6", "#111111", 42, "13sp", lambda *a: app.go("depts")))

    def save_sec(self, adm_un, ng, np, se, sp):
        app = App.get_running_app()
        app.admin_db["gate"] = ng.strip(); app.admin_db.setdefault("credentials", {})[adm_un] = np.strip()
        app.admin_db["smtp"] = {"email": se.strip(), "app_pass": sp.strip().replace(" ", "")}
        app.save_admin_db(); show_alert("Updated", "Saved!"); app.go("depts")

class DeptsScreen(BaseScreen):
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        hdr = f"GIRIRAJ ADHIKARY {LB}{app.st['role']}{RB}" if app.st["role"] == "ADMIN" else "NEXORA - STUDENT PORTAL"
        box.add_widget(make_label(hdr, "#FF0000", "16sp", True, "center", 36))
        top_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        top_row.add_widget(make_btn("KNOW THE FOUNDER", "#0b133b", "#00d4ff", 42, "12sp", lambda *a: app.go("founder")))
        top_row.add_widget(make_btn("MY ADMIN PROFILE" if app.st["role"] == "ADMIN" else "MY PROFILE", "#FF0000", "#FFFFFF", 42, "12sp", lambda *a: app.go("admin_profile" if app.st["role"] == "ADMIN" else "stu_profile")))
        box.add_widget(top_row)
        if app.st["role"] == "ADMIN":
            adm_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
            adm_row.add_widget(make_btn("MANAGE STUDENTS", "#f4f6fa", "#FF0000", 42, "12sp", lambda *a: app.go("stu_mgr")))
            adm_row.add_widget(make_btn("CHANGE PASSCODE", "#141414", "#00d4ff", 42, "12sp", lambda *a: app.go("change_passcode")))
            box.add_widget(adm_row)
        for d in ["Computer Science and Engineering (CSE)", "Electrical Engineering (EE)", "Mechanical Engineering (ME)", "Electronics and Communication Engineering (ECE)", "Civil Engineering (CE)"]:
            box.add_widget(make_btn(d, "#f4f6fa", "#111111", 56, "13sp", lambda *a, x=d: app.open_years(x)))
        box.add_widget(make_btn("LOGOUT", "#FF0000", "#FFFFFF", 48, "14sp", lambda *a: app.go("home")))

class YearsScreen(BaseScreen):
    dept = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, lambda: app.go("depts"), "<- Departments")
        box.add_widget(make_label(self.dept, "#FF0000", "15sp", True, "center", 44))
        for y in ["1st Year", "2nd Year", "3rd Year", "4th Year"]:
            box.add_widget(make_btn(y, "#f4f6fa", "#111111", 58, "16sp", (lambda *a, yr=y: app.open_sems(self.dept, yr, "")) if y == "1st Year" else (lambda *a, yr=y: app.open_syl_type(self.dept, yr))))

class SyllabusTypeScreen(BaseScreen):
    dept = ""; yr = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, lambda: app.open_years(self.dept), "<- Years")
        box.add_widget(make_label(f"{self.dept}\n{self.yr}", "#FF0000", "15sp", True, "center", 48))
        box.add_widget(make_btn("NEW SYLLABUS", "#FF0000", "#FFFFFF", 62, "16sp", lambda *a: app.open_sems(self.dept, self.yr, "NEW SYLLABUS")))
        box.add_widget(make_btn("OLD SYLLABUS", "#0b133b", "#00d4ff", 62, "16sp", lambda *a: app.open_sems(self.dept, self.yr, "OLD SYLLABUS")))

class SemsScreen(BaseScreen):
    dept = ""; yr = ""; syl = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, (lambda: app.open_years(self.dept)) if not self.syl else (lambda: app.open_syl_type(self.dept, self.yr)), "<- Back")
        box.add_widget(make_label(f"{self.dept}\n{self.yr}", "#FF0000", "15sp", True, "center", 50))
        mp = {"1st Year": ["1st Semester", "2nd Semester"], "2nd Year": ["3rd Semester", "4th Semester"], "3rd Year": ["5th Semester", "6th Semester"], "4th Year": ["7th Semester", "8th Semester"]}
        for sm in mp[self.yr]:
            box.add_widget(make_btn(sm, "#f4f6fa", "#111111", 62, "16sp", lambda *a, x=sm: app.open_subs(self.dept, self.yr, x, self.syl)))

class SubsScreen(BaseScreen):
    dept = ""; yr = ""; sm = ""; syl = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, lambda: app.open_sems(self.dept, self.yr, self.syl), "<- Semesters")
        box.add_widget(make_label(f"{self.yr} ({self.sm})", "#FF0000", "14sp", True, "center", 42))
        if app.st.get("role") == "ADMIN":
            box.add_widget(make_btn("+ ADD NEW SUBJECT", "#FF0000", "#FFFFFF", 46, "13sp", lambda *a: app.open_add_sub(self.dept, self.yr, self.sm, self.syl)))
        for idx, (nm, cd, up) in enumerate(app.get_sub_list(self.dept, self.sm, self.syl)):
            row = BoxLayout(size_hint_y=None, height=58, spacing=6)
            row.add_widget(make_btn(f"{nm}\nCode: {cd} | UPID: {up}", "#f4f6fa", "#111111", 56, "12sp", lambda *a, n=nm, c=cd, u=up: app.open_sub_pg(self.dept, self.yr, self.sm, n, c, u, "Syllabus", self.syl)))
            if app.st.get("role") == "ADMIN":
                del_b = make_btn("X", "#dddddd", "#FF0000", 56, "14sp", lambda *a, i=idx: (app.db["subs"][f"{self.dept}|{self.syl}|{self.sm}" if self.syl else f"{self.dept}|{self.sm}"].pop(i), app.save_db(), self.on_enter()))
                del_b.size_hint_x = None; del_b.width = 46; row.add_widget(del_b)
            box.add_widget(row)

class AddSubScreen(BaseScreen):
    dept = ""; yr = ""; sm = ""; syl = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, lambda: app.open_subs(self.dept, self.yr, self.sm, self.syl), "<- Back")
        ne = make_input("Subject Name"); ce = make_input("Subject Code"); ue = make_input("UPID")
        for w in (ne, ce, ue): box.add_widget(w)
        box.add_widget(make_btn("SAVE & OPEN SUBJECT", "#FF0000", "#FFFFFF", 50, "14sp", lambda *a: self.save_sub(ne.text, ce.text, ue.text)))

    def save_sub(self, nm, cd, up):
        app = App.get_running_app()
        n, c, u = nm.strip(), cd.strip().upper(), up.strip() or "000000"
        if n and c:
            app.get_sub_list(self.dept, self.sm, self.syl).append([n, c, u]); app.save_db()
            app.open_sub_pg(self.dept, self.yr, self.sm, n, c, u, "Syllabus", self.syl)

class SubjectDetailScreen(BaseScreen):
    dept = ""; yr = ""; sm = ""; nm = ""; cd = ""; up = ""; tab = "Syllabus"; syl = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, lambda: app.open_subs(self.dept, self.yr, self.sm, self.syl), "<- Subjects")
        mat_key = f"{self.dept}|{self.syl}|{self.cd}" if self.syl else f"{self.dept}|{self.cd}"
        app.db["mats"].setdefault(mat_key, {"Syllabus": [], "Notes": [], "PYQs": []})
        box.add_widget(make_label(f"{self.nm}\nCode: {self.cd} | UPID: {self.up}", "#FF0000", "14sp", True, "center", 48))
        bar = BoxLayout(size_hint_y=None, height=42, spacing=6)
        for t in ["Syllabus", "Notes", "PYQs"]:
            bar.add_widget(make_btn(t, "#FF0000" if t == self.tab else "#e6e6e6", "#FFFFFF" if t == self.tab else "#111111", 40, "13sp", lambda *a, x=t: app.open_sub_pg(self.dept, self.yr, self.sm, self.nm, self.cd, self.up, x, self.syl)))
        box.add_widget(bar)
        if app.st.get("role") == "ADMIN":
            ab1 = BoxLayout(size_hint_y=None, height=40, spacing=6)
            ab1.add_widget(make_btn("+ Offline File", "#FF0000", "#FFFFFF", 38, "12sp", lambda *a: filechooser.open_file(on_selection=lambda sel: (app.db["mats"][mat_key][self.tab].append(["OFFLINE FILE", os.path.basename(sel[0]), sel[0]]), app.save_db(), self.on_enter()) if sel else None) if HAS_PLYER else show_alert("Info", "Use Online File")))
            ab1.add_widget(make_btn("+ Online File", "#b30000", "#FFFFFF", 38, "12sp", lambda *a: app.open_add_mat("ONLINE_FILE", self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, self.syl)))
            box.add_widget(ab1)
            ab2 = BoxLayout(size_hint_y=None, height=40, spacing=6)
            ab2.add_widget(make_btn("+ Online Link", "#141414", "#FFFFFF", 38, "12sp", lambda *a: app.open_add_mat("ONLINE_LINK", self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, self.syl)))
            ab2.add_widget(make_btn("+ Custom Note", "#141414", "#FFFFFF", 38, "12sp", lambda *a: app.open_add_mat("CUSTOM_NOTE", self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, self.syl)))
            box.add_widget(ab2)
        for idx, (src, ttl, body) in enumerate(app.db["mats"][mat_key][self.tab]):
            row = BoxLayout(size_hint_y=None, height=48, spacing=6)
            row.add_widget(make_label(f"{LB}{src}{RB} {ttl}", "#111111", "12sp", True, "left", 46))
            vb = make_btn("View", "#FF0000", "#FFFFFF", 42, "12sp", lambda *a, sr=src, tl=ttl, bd=body: app.open_view_mat(self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, sr, tl, bd, self.syl))
            vb.size_hint_x = None; vb.width = 65; row.add_widget(vb)
            box.add_widget(row)

class AddMaterialScreen(BaseScreen):
    mode = "ONLINE_FILE"; dept = ""; yr = ""; sm = ""; nm = ""; cd = ""; up = ""; tab = "Syllabus"; syl = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, lambda: app.open_sub_pg(self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, self.syl), "<- Back")
        te = make_input("Title", f"{self.nm} {self.tab}"); box.add_widget(te)
        if self.mode in ("ONLINE_FILE", "ONLINE_LINK"):
            ue = make_input("https://", "https://"); box.add_widget(ue)
            box.add_widget(make_btn("PUBLISH", "#FF0000", "#FFFFFF", 50, "14sp", lambda *a: self.publish_url(te.text, ue.text)))
        else:
            bt = TextInput(hint_text="Write note...", size_hint_y=None, height=180)
            box.add_widget(bt)
            box.add_widget(make_btn("PUBLISH NOTE", "#FF0000", "#FFFFFF", 50, "14sp", lambda *a: (app.db["mats"][f"{self.dept}|{self.syl}|{self.cd}" if self.syl else f"{self.dept}|{self.cd}"][self.tab].append(["CUSTOM NOTE", te.text.strip(), bt.text.strip()]), app.save_db(), app.open_sub_pg(self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, self.syl))))

    def publish_url(self, ttl, url):
        app = App.get_running_app()
        mat_key = f"{self.dept}|{self.syl}|{self.cd}" if self.syl else f"{self.dept}|{self.cd}"
        app.db["mats"][mat_key][self.tab].append(["ONLINE LINK", ttl.strip() or "Link", url.strip()]); app.save_db()
        app.open_sub_pg(self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, self.syl)

class ViewMaterialScreen(BaseScreen):
    dept = ""; yr = ""; sm = ""; nm = ""; cd = ""; up = ""; tab = "Syllabus"; src = ""; ttl = ""; body = ""; syl = ""
    def on_enter(self):
        app = App.get_running_app()
        box = self.build_scroll_page("#FFFFFF")
        self.add_top_nav(box, lambda: app.open_sub_pg(self.dept, self.yr, self.sm, self.nm, self.cd, self.up, self.tab, self.syl), f"<- {self.tab}")
        box.add_widget(make_label(self.ttl, "#FF0000", "16sp", True, "center", 42))
        box.add_widget(make_label(self.body, "#111111", "13sp", False, "left"))
        if self.src == "ONLINE LINK":
            box.add_widget(make_btn("OPEN LINK IN BROWSER", "#FF0000", "#FFFFFF", 48, "14sp", lambda *a: webbrowser.open(self.body.strip())))

class NexoraApp(App):
    def build(self):
        self.title = "NEXORA - Giriraj Adhikary"
        self.base_dir = self.user_data_dir; os.makedirs(self.base_dir, exist_ok=True)
        self.dbf = os.path.join(self.base_dir, "giriraj_data.json")
        self.admin_dbf = os.path.join(self.base_dir, "giriraj_admin_db.json")
        self.files_dir = os.path.join(self.base_dir, "giriraj_files")
        self.admin_db = self.load_admin_db(); self.db = self.load_db()
        self.st = {"role": "", "user": ""}
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        for scr in [SplashScreen(name="splash"), HomeScreen(name="home"), AdminGateScreen(name="admin_gate"), AdminRegisterScreen(name="admin_reg"), AuthScreen(name="auth"), ForgotScreen(name="forgot"), VerifyOtpScreen(name="verify_otp"), FounderScreen(name="founder"), EditBioScreen(name="edit_bio"), MediaScreen(name="media"), StudentProfileScreen(name="stu_profile"), StudentEditProfileScreen(name="stu_edit_profile"), AdminProfileScreen(name="admin_profile"), ManageStudentsScreen(name="stu_mgr"), ChangePasscodeScreen(name="change_passcode"), DeptsScreen(name="depts"), YearsScreen(name="years"), SyllabusTypeScreen(name="syl_type"), SemsScreen(name="sems"), SubsScreen(name="subs"), AddSubScreen(name="add_sub"), SubjectDetailScreen(name="sub_pg"), AddMaterialScreen(name="add_mat"), ViewMaterialScreen(name="view_mat")]:
            self.sm.add_widget(scr)
        self.sm.current = "splash"
        return self.sm

    def go(self, s):
        scr = self.sm.get_screen(s)
        scr.on_enter() if self.sm.current == s else setattr(self.sm, "current", s)
    def open_auth(self, r): self.sm.get_screen("auth").role = r; self.go("auth")
    def open_media(self, k): self.sm.get_screen("media").key = k; self.go("media")
    def open_verify_otp(self, te, sm): s = self.sm.get_screen("verify_otp"); s.target_email = te; s.sender_mail = sm; self.go("verify_otp")
    def open_stu_profile_edit(self, u, ft=True): s = self.sm.get_screen("stu_edit_profile"); s.un = u; s.first_time = ft; self.go("stu_edit_profile")
    def open_years(self, d): self.sm.get_screen("years").dept = d; self.go("years")
    def open_syl_type(self, d, y): s = self.sm.get_screen("syl_type"); s.dept = d; s.yr = y; self.go("syl_type")
    def open_sems(self, d, y, syl=""): s = self.sm.get_screen("sems"); s.dept = d; s.yr = y; s.syl = syl; self.go("sems")
    def open_subs(self, d, y, sm, syl=""): s = self.sm.get_screen("subs"); s.dept = d; s.yr = y; s.sm = sm; s.syl = syl; self.go("subs")
    def open_add_sub(self, d, y, sm, syl=""): s = self.sm.get_screen("add_sub"); s.dept = d; s.yr = y; s.sm = sm; s.syl = syl; self.go("add_sub")
    def open_sub_pg(self, d, y, sm, nm, cd, up, tab="Syllabus", syl=""): s = self.sm.get_screen("sub_pg"); s.dept=d; s.yr=y; s.sm=sm; s.nm=nm; s.cd=cd; s.up=up; s.tab=tab; s.syl=syl; self.go("sub_pg")
    def open_add_mat(self, m, d, y, sm, nm, cd, up, tab, syl=""): s = self.sm.get_screen("add_mat"); s.mode=m; s.dept=d; s.yr=y; s.sm=sm; s.nm=nm; s.cd=cd; s.up=up; s.tab=tab; s.syl=syl; self.go("add_mat")
    def open_view_mat(self, d, y, sm, nm, cd, up, tab, src, ttl, body, syl=""): s = self.sm.get_screen("view_mat"); s.dept=d; s.yr=y; s.sm=sm; s.nm=nm; s.cd=cd; s.up=up; s.tab=tab; s.src=src; s.ttl=ttl; s.body=body; s.syl=syl; self.go("view_mat")
    def enlarge_photo(self, img_path, title_txt):
        box = BoxLayout(orientation="vertical", padding=10, spacing=8); box.add_widget(KivyImage(source=img_path, allow_stretch=True, keep_ratio=True))
        btn = make_btn("Close", "#FF0000", "#FFFFFF", 40, "13sp"); box.add_widget(btn); pop = Popup(title=title_txt, content=box, size_hint=(0.88, 0.72)); btn.bind(on_release=pop.dismiss); pop.open()

    def get_sub_list(self, dept, sm, syl=""):
        self.db.setdefault("subs", {})
        key = f"{dept}|{syl}|{sm}" if syl else f"{dept}|{sm}"
        if key not in self.db["subs"]:
            self.db["subs"][key] = [list(x) for x in DEFAULT_EE_SUBS.get(sm, [])] if ("(EE)" in dept and (not syl or syl == "OLD SYLLABUS")) else []
            self.save_db()
        return self.db["subs"][key]

    def load_admin_db(self):
        defaults = {"registered": False, "gate": "GIRIRAJ2026", "credentials": {"giriraj": "1234"}, "profile": {"username": "", "name": "Giriraj Adhikary", "role": "Founder & Creator of NEXORA", "dept": "Electrical Engineering (EE)", "college": "", "mobile": "", "email": "girirajadhikary100@gmail.com", "pfp": ""}, "smtp": {"email": "girirajadhikary100@gmail.com", "app_pass": ""}}
        if os.path.exists(self.admin_dbf):
            try:
                d = json.load(open(self.admin_dbf, "r", encoding="utf-8"))
                for k, v in defaults.items(): d.setdefault(k, v)
                return d
            except Exception: pass
        return defaults

    def save_admin_db(self):
        try: json.dump(self.admin_db, open(self.admin_dbf, "w", encoding="utf-8"), indent=2)
        except Exception: pass

    def load_db(self):
        defaults = [("students", {"student": "1234"}), ("profiles", {}), ("students_db", {}), ("mats", {}), ("subs", {}), ("bg", ""), ("pfp", ""), ("bio", BIO)]
        if os.path.exists(self.dbf):
            try:
                d = json.load(open(self.dbf, "r", encoding="utf-8"))
                for k, v in defaults: d.setdefault(k, v)
                return d
            except Exception: pass
        out = {k: v for k, v in defaults}
        out["students_db"] = {"student": {"username": "student", "password": "1234", "name": "", "dept": "", "college": "", "mobile": "", "email": "", "pfp": ""}}
        return out

    def save_db(self):
        try:
            for u, rec in self.db.setdefault("students_db", {}).items():
                self.db.setdefault("students", {})[u] = rec.get("password", ""); self.db.setdefault("profiles", {})[u] = rec
            json.dump(self.db, open(self.dbf, "w", encoding="utf-8"), indent=2)
        except Exception: pass

    def send_sys_email(self, to_addr, subject, body_txt):
        smtp_cfg = self.admin_db.get("smtp", {})
        sender = (smtp_cfg.get("email") or "girirajadhikary100@gmail.com").strip()
        app_pw = smtp_cfg.get("app_pass", "").strip().replace(" ", "")
        if not app_pw: return False, "App Password empty"
        msg = EmailMessage(); msg["Subject"] = subject; msg["From"] = f"NEXORA Portal <{sender}>"; msg["To"] = to_addr.strip(); msg.set_content(body_txt)
        try:
            with smtplib.SMTP_SSL("://gmail.com", 465, context=ssl._create_unverified_context(), timeout=15) as srv:
                srv.login(sender, app_pw); srv.send_message(msg)
            return True, "Sent"
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    try:
        NexoraApp().run()
    except Exception:
        import traceback
        err_txt = traceback.format_exc()
        from kivy.base import runTouchApp
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label
        sv = ScrollView()
        lbl = Label(text="ERROR DETAILS:\n\n" + err_txt, color=(1, 1, 0, 1), font_size="14sp", size_hint_y=None)
        lbl.bind(texture_size=lambda i, v: setattr(i, "height", v[1] + 40), size=lambda i, v: setattr(i, "text_size", (v[0] - 20, None)))
        sv.add_widget(lbl)
        runTouchApp(sv)
