import matplotlib.pyplot as plt
import numpy as np
import ast


class Loglistener:

    def __init__(self):
        self.logs = list()

    def write(self, record):
        try:
            dic = ast.literal_eval(record)
            self.logs.append(dic)
        except:
            pass

    def flush(self):
        pass

    @staticmethod
    def remove_loglisteners(logger):
        for handler in logger.handlers:
            if isinstance(handler.stream, Loglistener):
                logger.removeHandler(handler)

    @staticmethod
    def get_first_loglistener(logger):
        try:
            for handler in logger.handlers:
                if isinstance(handler.stream, Loglistener):
                    return handler
        except ValueError:
            print("No loglisteners at hand")
            raise





class SubStringer:

    def __init__(self, *args):
        if len(args)==2:
            self.interval = [args[0], args[1]]
        else:
            self.interval = []

    def change(self, string):
        if len(self.interval)==2:
            return string[self.interval[0]: self.interval[1]]
        else:
            return string


class GraphicGen:


    def bar_plot(self, bars, outname, yerr = None):
        fig, ax = plt.subplots()
        ax.errorbar(range(len(bars)), bars, yerr)
        fig.savefig(outname)

    def histogram_subplots(self, samples_list, outname, rows=2, cols=1, bins=50, xlim=None):
        assert(len(samples_list) <= rows*cols)
        size_factor = 4
        fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(cols*size_factor, rows*size_factor))
        axes = np.array(axes)
        for samples, ax in zip(samples_list, axes.reshape(-1)[0:len(samples_list)]):
            ax.hist(samples, bins=bins)
            if xlim is not None:
                ax.set_xlim(xlim)
        fig.savefig(outname)

    def trend_subplots(self, xs, ys, outname, rows=2, cols=1):
        assert (len(xs) <= rows * cols)
        size_factor = 5
        fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(cols * size_factor, rows * size_factor))
        axes = np.array(axes)
        for x, y, ax in zip(xs, ys, axes.reshape(-1)[0:len(xs)]):
            ax.plot(x, y, linestyle='None', marker='.',)
        fig.savefig(outname)

    def hist_and_trends(self, x, ys, samples, outname, rows=1, cols=1, xlim=None, bins=20):
        size_factor = 5
        fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(cols * size_factor, rows * size_factor))
        # axes = np.array(axes)
        axes.hist(samples, density=True, bins=bins)
        for y in ys:
            axes.plot(x, y)
        if xlim != None:
            axes.set_xlim(xlim)
        fig.savefig(outname)


class DataServer:

    def __init__(self, pack):
        self.pack = pack

    def table_layer_count_context(self):
        lbs, ubs = self.get_lbs_ubs()

        #find object column
        sheet = self.pack.datasheet_set.get(sheet_name="Property Profile")
        keyvals = sheet.keyval_set.filter(tag="NR")
        if keyvals:
            cols = np.array([float(keyval.value) for keyval in keyvals.order_by("chrono")])

            keyvals = sheet.keyval_set.filter(tag="ETB")
            bands = list()
            for dist in keyvals.distinct("key"):
                bands.append([float(keyval.value) for keyval in keyvals.filter(key=dist.key).order_by("chrono")])
            sm = np.argsort([bands[0][0], bands[1][0]])
            #bool = bands[sm[1]] > lbs[0]
            obj_in_lay = [int(np.sum(cols[bands[sm[1]] > lb])) for lb in lbs]
            tuple = (lbs.tolist(), ubs.tolist(), obj_in_lay)
            cont_dict = {
                "lbs": lbs.tolist(),
                "ubs": ubs.tolist(),
                "obj_in_layer": obj_in_lay
            }
            return cont_dict
        else:
            cont_dict = {
                "lbs": [],
                "ubs": [],
                "obj_in_layer": []
            }
            return cont_dict

    def histogram_layer_detail_context(self):
        lbs, ubs = self.get_lbs_ubs()
        sheet = self.pack.datasheet_set.get(sheet_name="Property Profile")
        keyvals = sheet.keyval_set.filter(tag="NR")
        if keyvals:
            cols = [float(keyval.value) for keyval in keyvals.order_by("chrono")]

            keyvals = sheet.keyval_set.filter(tag="ETB")
            bands = list()
            for dist in keyvals.distinct("key"):
                bands.append([float(keyval.value) for keyval in keyvals.filter(key=dist.key).order_by("chrono")])
            sm = np.argsort([bands[0][0], bands[1][0]])

            tags = list()
            for ub in bands[sm[1]]:
                if ub < ubs[0]:
                    tags.append("layer 1")
                elif ub < lbs[1]:
                    tags.append("hole 1")
                elif ub < ubs[1]:
                    tags.append("layer 2")
                elif ub < lbs[2]:
                    tags.append("hole 2")
                else:
                    tags.append("layer 3")
            strings = [str(l_band) + " - " + str(u_band) for l_band, u_band in zip(bands[0], bands[1])]
            ret = {
                "strings": strings,
                "cols": cols,
                "tags": tags
            }
            return ret
        else:
            ret = {
                "strings": list(),
                "cols": list(),
                "tags": list()
            }
            return ret

    def table_layer_loss_context(self):
        lbs, ubs = self.get_lbs_ubs()
        sheet = self.pack.datasheet_set.get(sheet_name="Per Risk Losses")
        years = [kv.value for kv in sheet.keyval_set.filter(tag="YR").distinct("value")]
        year_losses = dict()
        for year in years:
            chronos = [kv.chrono for kv in sheet.keyval_set.filter(tag="YR").filter(value=year)]
            year_losses[year] = np.array([float(kv.value) for kv in sheet.keyval_set.filter(tag="LO").filter(chrono__in=chronos).order_by("chrono")])

        layer_losses = list()
        for i in range(len(lbs)):
            if year_losses.values():
                layer_losses.append(list())
            for losses in year_losses.values():
                temp_list = np.minimum(losses[losses > lbs[i]]-lbs[i], ubs[i]-lbs[i])
                layer_losses[i].append((np.sum(temp_list), temp_list.size))
        years = [int(float(year)) for year in years]
        ret = {
            "lbs": lbs.tolist(),
            "ubs": ubs.tolist(),
            "years": years,
            "layer_losses": layer_losses
        }

        return ret

    def table_premium_segment_context(self):
        sheet = self.pack.datasheet_set.get(sheet_name="Premium Income")
        # get the right rows
        rows = [kv.chrono for kv in sheet.keyval_set.filter(tag="TAG").filter(value="Total PD+BI")]
        # get headers of tag=Segment
        headers = [kv.key for kv in sheet.keyval_set.filter(tag="SEG").distinct("key")]
        prem_seg_list = list()
        for header in headers:
            prems = [float(kv.value) for kv in sheet.keyval_set.filter(key=header).filter(chrono__in=rows).order_by("-chrono")]
            prem_seg_list.append(prems)
        years = [int(float(kv.value)) for kv in sheet.keyval_set.filter(tag="YR").filter(chrono__in=rows).order_by("-chrono")]
        ret = {
            "years": years,
            "prem_seg_list": prem_seg_list,
            "headers": headers
        }

        return ret

    def table_burning_cost_context(self, losses):
        lbs, ubs = self.get_lbs_ubs()

        #find object column
        sheet = self.pack.datasheet_set.get(sheet_name="Property Profile")
        keyvals = sheet.keyval_set.filter(tag="PR")
        if keyvals:
            cols = np.array([float(keyval.value) for keyval in keyvals.order_by("chrono")])

            keyvals = sheet.keyval_set.filter(tag="ETB")
            bands = list()
            for dist in keyvals.distinct("key"):
                bands.append([float(keyval.value) for keyval in keyvals.filter(key=dist.key).order_by("chrono")])
            sm = np.argsort([bands[0][0], bands[1][0]])
            prm_in_lay = [float(np.sum(cols[bands[sm[1]] > lb])) for lb in lbs]
            ratio = [loss/prm for loss, prm in zip(losses, prm_in_lay)]

            ret = {
                "lbs": lbs.tolist(),
                "ubs": ubs.tolist(),
                "ratios": ratio
            }
            return ret
        else:
            ret = {
                "lbs": [],
                "ubs": [],
                "ratios": []
            }
            return ret

    def get_lbs_ubs(self):
        layers = self.pack.xllayer_set.all()
        for layer in layers:
            pass
        lbs = np.array([layer.lb for layer in layers])
        lbs.sort()
        ubs = np.array([layer.ub for layer in layers])
        ubs.sort()
        return lbs, ubs


        #do computation
