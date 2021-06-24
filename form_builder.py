import tkinter as tk
from tkinter import ttk
import jsonschema

from scrollable_frame import ScrollableFrame
from tooltip import ToolTip
from validation import validate as json_validate
from read_schema import read_with_id


type_conversion = {
    "object": dict,
    "integer": int,
    "string": str,
    "array": list,
    "boolean": bool,
    "null": type(None)
}


def deep_eval(structure):
    t = type(structure)
    if t == dict:
        return {k: deep_eval(structure[k]) for k in structure}
    if t == list:
        return [deep_eval(k) for k in structure]
    else:
        return structure()


class Trash:
    pass


trash = Trash()


def deep_clean(e_structure):
    if e_structure == trash:
        return trash
    elif isinstance(e_structure, list):
        return [deep_clean(k) for k in e_structure]
    elif isinstance(e_structure, dict):
        res = {}
        for k in e_structure:
            dck = deep_clean(e_structure[k])
            if dck != trash:
                res[k] = dck
        return res
    else:
        return e_structure


class Form:
    def __init__(self, schema):
        self.schema = schema
        self.answer = {}
        self.answer_interface = {}
        self.validated = False
        self.window = tk.Tk()

        btn_close = tk.Button(master=self.window, text="Validate", command=self.validate_factory())
        scr_frame = ScrollableFrame(master=self.window)

        scr_frame.pack(fill="both", expand=True)
        btn_close.pack()

        brf = self.build_rec_form(self.schema, scr_frame)
        self.answer_interface = brf["res_method"]

    def run(self):
        self.window.mainloop()
        if self.validated:
            return self.answer
        else:
            raise ValueError

    def validate_factory(self):
        def validate():
            self.answer = deep_clean(deep_eval(self.answer_interface))
            try:
                json_validate(instance=self.answer, schema=self.schema)
                self.window.destroy()
                self.validated = True
            except jsonschema.exceptions.ValidationError as e:
                print(self.validated)
                print("schema not validated:")
                print(e)
        return validate

    def build_rec_form(self, schema, master):
        if "$ref" in schema:
            return self.build_rec_form(read_with_id(schema['$ref']), master)

        elif "enum" in schema:
            frm_subform = tk.Frame(master=master)
            res_method = self.build_enum_form(schema["enum"], frm_subform)
            frm_subform.pack(anchor=tk.W)
            return {"res_method": res_method, "subframe": frm_subform}

        elif "isPropertyOf" in schema:
            # not a standard property of json-schema
            frm_subform = tk.Frame(master=master)
            # keys = [k for k in unref_schema(schema["isPropertyOf"])]
            keys = [k for k in schema["isPropertyOf"]]
            res_method = self.build_enum_form(keys, frm_subform)
            frm_subform.pack(anchor=tk.W)
            return {"res_method": res_method, "subframe": frm_subform}

        elif "data" in schema:
            # not a standard property of json-schema
            data = schema["data"]
            subschema = {
                d: read_url(data[d], default_document=deep_eval(deep_clean(self.answer_interface)))
                for d in data
            }
            merge_schema = {**subschema, **schema}
            del merge_schema["data"]
            return self.build_rec_form(merge_schema, master)

        elif "type" in schema:
            item_type = schema["type"]
            frm_subform = tk.Frame(master=master)

            t_python = type_conversion[item_type]

            if t_python == str:
                res_method = self.build_str_form(schema, frm_subform)
            elif t_python == int:
                res_method = self.build_int_form(schema, frm_subform)
            elif t_python == dict:
                res_method = self.build_dict_form(schema, frm_subform)
            elif t_python == list:
                res_method = self.build_list_form(schema, frm_subform)
            elif t_python == bool:
                res_method = self.build_bool_form(schema, frm_subform)
            elif t_python == type(None):
                res_method = lambda: None
            else:
                print(f"type not supported: {t_python}")

            frm_subform.pack(anchor=tk.W)
            return {"res_method": res_method, "subframe": frm_subform}

        else:
            print("wut?")
            print(schema)

    def build_dict_form(self, schema, master):
        answers = {}
        properties = schema.get("properties", {})
        additional_properties = schema.get("additionalProperties", None)
        if "maxProperties" not in schema:
            for k in properties:
                frm_k = tk.Frame(master=master, bd=4, highlightbackground="red", highlightthickness=0.5)
                frm_title = tk.Frame(master=frm_k)
                lbl_k = tk.Label(master=frm_title, text=k)
                lbl_k.pack(side=tk.LEFT)

                if "description" in properties[k]:
                    helper_text = properties[k]["description"]
                    lbl_tooltip = tk.Label(master=frm_title, text="?")
                    ToolTip(lbl_tooltip, helper_text)
                    lbl_tooltip.pack()

                frm_title.pack()
                answers[k] = self.build_rec_form(properties[k], frm_k)["res_method"]
                frm_k.pack(anchor=tk.W)

            if additional_properties is not None:
                frm_add = tk.Frame(master=master)
                btn_add_item = tk.Button(master=frm_add, text="+")
                btn_add_item.pack(side=tk.LEFT)

                if "propertyNames" in schema:
                    brf = self.build_rec_form(schema["propertyNames"], frm_add)
                    ent_add_item = brf["subframe"]
                    get_method = brf["res_method"]
                else:
                    ent_add_item = tk.Entry(master=frm_add)
                    get_method = ent_add_item.get

                def remove_item(frm, old_key):
                    def res():
                        frm.destroy()
                        del answers[old_key]

                    return res

                def add_item():
                    new_key = get_method()
                    # new_key = ent_add_item.get()

                    frm_k = tk.Frame(master=master, bd=4, highlightbackground="red", highlightthickness=0.5)
                    btn_delete = tk.Button(master=frm_k, text="del", command=remove_item(frm_k, new_key))
                    btn_delete.pack(side=tk.LEFT)

                    lbl_k = tk.Label(master=frm_k, text=new_key)
                    lbl_k.pack()
                    answers[new_key] = self.build_rec_form(additional_properties, frm_k)["res_method"]
                    try:
                        ent_add_item.delete(0, 'end')
                    except AttributeError:
                        pass
                    frm_k.pack(anchor=tk.W)

                btn_add_item['command'] = add_item
                ent_add_item.pack(side=tk.LEFT)
                frm_add.pack(side=tk.BOTTOM)

        else:
            bridge = BtnsBridge(schema["maxProperties"])
            for k in properties:
                frm_k = tk.Frame(master=master, bd=4, highlightbackground="red", highlightthickness=0.5)
                frm_title = tk.Frame(master=frm_k)
                lbl_k = tk.Label(master=frm_title, text=k)
                lbl_k.pack(side=tk.LEFT)

                btn_k = tk.Button(master=frm_k, text="Choose")
                bcf = BtnHandler(k, properties[k], frm_k, btn_k, answers, bridge)
                bridge.btn_collection.append(bcf)
                btn_k['command'] = bcf.get_cmd(form=self)

                if "description" in properties[k]:
                    helper_text = properties[k]["description"]
                    lbl_tooltip = tk.Label(master=frm_title, text="?")
                    ToolTip(lbl_tooltip, helper_text)
                    lbl_tooltip.pack()

                frm_title.pack()
                btn_k.pack()
                frm_k.pack(anchor=tk.W)

            # TODO: if additional_properties is not None

        return answers

    def build_list_form(self, schema, master):
        answers = []
        item_properties = schema["items"]

        def add_item():
            frm_k = tk.Frame(master=master, bd=4, highlightbackground="red", highlightthickness=0.5)
            btn_delete = tk.Button(master=frm_k, text="del", command=frm_k.destroy)
            btn_delete.pack(side=tk.LEFT)
            answers.append(self.build_rec_form(item_properties, frm_k)["res_method"])
            frm_k.pack(anchor=tk.W)

        btn_add_item = tk.Button(master=master, text="+", command=add_item)
        btn_add_item.pack(side=tk.BOTTOM)
        return answers

    def build_str_form(self, schema, master):
        ent_answer = tk.Entry(master=master)
        ent_answer.pack()
        return ent_answer.get

    def build_int_form(self, schema, master):
        ent_answer = tk.Entry(master=master)
        ent_answer.pack()

        def res():
            ans = ent_answer.get()
            if ans == "":
                return trash
            else:
                return int(ans)

        return res

    def build_bool_form(self, schema, master):
        answer = tk.IntVar()
        ent_answer = tk.Checkbutton(master=master, variable=answer)
        ent_answer.pack()

        def res(): return bool(answer.get())

        return res

    def build_enum_form(self, values, master):
        ent_answer = tk.ttk.Combobox(master=master, state="readonly", values=values)
        ent_answer.pack()
        return ent_answer.get


class BtnsBridge:
    def __init__(self, max_activated):
        self.btn_collection = []
        self.max_activated = max_activated

    def actualize(self):
        if len([b for b in self.btn_collection if b.activated]) >= self.max_activated:
            for b in self.btn_collection:
                if not b.activated:
                    b.lock()
        else:
            for b in self.btn_collection:
                b.unlock()


class BtnHandler:
    def __init__(self, k, k_properties, k_frame, btn_k, answers, bridge):
        self.k = k
        self.k_prop = k_properties
        self.k_frame = k_frame
        self.k_btn = btn_k
        self.answers = answers
        self.bridge = bridge

        self.subframe = None
        self.activated = False

    def get_cmd(self, form):
        def res():
            if self.activated:
                del self.answers[self.k]
                self.subframe.destroy()
                self.k_btn['text'] = "Choose"
                self.activated = False
            else:
                brf = form.build_rec_form(self.k_prop, self.k_frame)
                self.answers[self.k] = brf["res_method"]
                self.subframe = brf["subframe"]
                self.k_btn['text'] = "Cancel"
                self.activated = True
            self.bridge.actualize()
        return res

    def lock(self):
        self.k_btn["state"] = tk.DISABLED

    def unlock(self):
        self.k_btn["state"] = tk.ACTIVE


def read_fragment(fragment, document):
    path = []
    if fragment == "":
        print("empty fragment")
        # return document
    elif fragment.startswith("#"):
        f = fragment.lstrip("#").lstrip("/")
        path = f.split("/")
    else:
        path = fragment.lstrip("/").split("/")

    doc = document
    for k in path:
        doc = doc[k]
    return doc


def read_url(url, default_document):
    s = url.split("#")
    if len(s) == 1:
        try:
            return read_fragment(s[0], default_document)
        except KeyError:
            return read_with_id(s[0])
    else:
        if s[0] == "":
            d = default_document
        else:
            d = read_with_id(s[0])
        return read_fragment(s[1], d)


if __name__ == "__main__":
    import json

    with open('../resources/state_schema.json', 'r', encoding="utf-8") as fsche:
        schema = json.load(fsche)
    ans = Form(schema).run()
