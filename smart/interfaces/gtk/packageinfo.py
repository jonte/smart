#
# Copyright (c) 2004 Conectiva, Inc.
#
# Written by Gustavo Niemeyer <niemeyer@conectiva.com>
#
# This file is part of Smart Package Manager.
#
# Smart Package Manager is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# Smart Package Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Smart Package Manager; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
from smart.interfaces.gtk.packageview import GtkPackageView
from smart.util.strtools import sizeToStr
from smart import *
import gobject, gtk, pango
import subprocess

class GtkPackageInfo(gtk.Alignment):
    hovering_over_link = False
    hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
    regular_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)

    def __init__(self):
        gtk.Alignment.__init__(self, 0.5, 0.5, 1.0, 1.0)

        self._pkg = None
        self._changeset = None

        font = self.style.font_desc.copy()
        font.set_size(font.get_size()-pango.SCALE)

        boldfont = font.copy()
        boldfont.set_weight(pango.WEIGHT_BOLD)

        self._notebook = gtk.Notebook()
        self._notebook.show()
        self.add(self._notebook)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        #sw.set_border_width(5)
        sw.show()

        table = gtk.Table()
        table.set_row_spacings(2)
        table.set_col_spacings(5)
        table.set_border_width(5)
        table.show()
        sw.add_with_viewport(table)

        self._info = type("Info", (), {})()

        attrsleft = pango.AttrList()
        attrsleft.insert(pango.AttrFontDesc(font, 0, -1))
        attrsright = pango.AttrList()
        attrsright.insert(pango.AttrFontDesc(boldfont, 0, -1))

        row = 0
        for attr, text in [("status", _("Status:")),
                           ("priority", _("Priority:")),
                           ("group", _("Group:")),
                           ("installedsize", _("Installed Size:")),
                           ("channels", _("Channels:"))]:
            label = gtk.Label(text)
            label.set_attributes(attrsleft)
            if attr == "channels":
                label.set_alignment(1.0, 0.0)
            else:
                label.set_alignment(1.0, 0.5)
            label.show()
            table.attach(label, 0, 1, row, row+1, gtk.FILL, gtk.FILL)
            setattr(self._info, attr+"_label", label)
            label = gtk.Label()
            label.set_attributes(attrsright)
            label.set_alignment(0.0, 0.5)
            label.show()
            table.attach(label, 1, 2, row, row+1, gtk.FILL, gtk.FILL)
            setattr(self._info, attr, label)
            row += 1

        label = gtk.Label(_("General"))
        self._notebook.append_page(sw, label)


        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.set_border_width(5)
        sw.show()

        self._descrtv = gtk.TextView()
        self._descrtv.set_editable(False)
        self._descrtv.set_cursor_visible(False)
        self._descrtv.set_left_margin(5)
        self._descrtv.set_right_margin(5)
        self._descrtv.show()
        buffer = self._descrtv.get_buffer()
        buffer.create_tag("description", font_desc=font)
        buffer.create_tag("summary", font_desc=boldfont)
        sw.add(self._descrtv)

        label = gtk.Label(_("Description"))
        self._notebook.append_page(sw, label)


        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.set_border_width(5)
        sw.show()

        self._conttv = gtk.TextView()
        self._conttv.set_editable(False)
        self._conttv.set_cursor_visible(False)
        self._conttv.set_left_margin(5)
        self._conttv.set_right_margin(5)
        self._conttv.show()
        buffer = self._conttv.get_buffer()
        buffer.create_tag("content", font_desc=font)
        sw.add(self._conttv)

        label = gtk.Label(_("Content"))
        self._notebook.append_page(sw, label)


        self._relations = GtkPackageView()
        self._relations.set_border_width(5)
        self._relations.getTreeView().set_headers_visible(False)
        self._relations.show()

        label = gtk.Label(_("Relations"))
        self._notebook.append_page(self._relations, label)


        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_border_width(5)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.show()

        model = gtk.ListStore(gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING)
        self._urls = gtk.TreeView(model)
        self._urls.set_headers_visible(False)
        self._urls.show()
        renderer = gtk.CellRendererText()
        renderer.set_property("font-desc", font)
        self._urls.insert_column_with_attributes(-1, _("Channel"),
                                                 renderer, text=0)
        self._urls.insert_column_with_attributes(-1, _("Size"),
                                                 renderer, text=1)
        self._urls.insert_column_with_attributes(-1, _("URL"),
                                                 renderer, text=2)
        sw.add(self._urls)

        label = gtk.Label(_("URLs"))
        self._notebook.append_page(sw, label)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.set_border_width(5)
        sw.show()

        self._reftv = gtk.TextView()
        self._reftv.set_editable(False)
        self._reftv.set_cursor_visible(False)
        self._reftv.set_left_margin(5)
        self._reftv.set_right_margin(5)
        self._reftv.connect("motion-notify-event", self.motion_notify_event)
        self._reftv.connect("event-after", self.event_after)
        self._reftv.show()
        buffer = self._reftv.get_buffer()
        buffer.create_tag("reference", font_desc=font)
        sw.add(self._reftv)

        label = gtk.Label(_("Reference"))
        self._notebook.append_page(sw, label)

        self._notebook.connect("switch_page", self._switchPage)

    '''
    this motion_notify_event/event_after code was adopted from hypertext demo
    '''

    # Update the cursor image if the pointer moved.
    def motion_notify_event(self, text_view, event):
        x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
            int(event.x), int(event.y))
        self.set_cursor_if_appropriate(text_view, x, y)
        text_view.window.get_pointer()
        return False

    # Looks at all tags covering the position (x, y) in the text view,
    # and if one of them is a link, change the cursor to the "hands" cursor
    # typically used by web browsers.
    def set_cursor_if_appropriate(self, text_view, x, y):
        hovering = False

        buffer = text_view.get_buffer()
        iter = text_view.get_iter_at_location(x, y)

        tags = iter.get_tags()
        for tag in tags:
            url = tag.get_data("url")
            if url:
                hovering = True
                break

        if hovering != self.hovering_over_link:
            self.hovering_over_link = hovering

        if self.hovering_over_link:
            text_view.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(self.hand_cursor)
        else:
            text_view.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(self.regular_cursor)

    def event_after(self, text_view, event):
        if event.type != gtk.gdk.BUTTON_RELEASE:
            return False
        if event.button != 1:
            return False
        buffer = text_view.get_buffer()

        # we shouldn't follow a link if the user has selected something
        try:
            start, end = buffer.get_selection_bounds()
        except ValueError:
            # If there is nothing selected, None is return
            pass
        else:
            if start.get_offset() != end.get_offset():
                return False

        x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
            int(event.x), int(event.y))
        iter = text_view.get_iter_at_location(x, y)

        self.follow_if_link(text_view, iter)
        return False

    def follow_if_link(self, text_view, iter):
        ''' Looks at all tags covering the position of iter in the text view,
            and if one of them is a link, follow it by opening the url.
        '''
        tags = iter.get_tags()
        for tag in tags:
            url = tag.get_data("url")
            if url:
                self.open_url(url)
                break

    def open_url(self, url):
        ''' Open the specified URL in a browser (try a few alternatives) '''
        for browser in ['gnome-open', 'x-www-browser', 'firefox']:
            command = [browser, url]
            retcode = subprocess.call(command)
            if retcode == 0:
                break

    def _switchPage(self, notebook, page, pagenum):
        self.setPackage(self._pkg, _pagenum=pagenum)

    def setChangeSet(self, changeset):
        self._changeset = changeset

    def setPackage(self, pkg, _pagenum=None):

        self._pkg = pkg

        if _pagenum is not None:
            num = _pagenum
        else:
            num = self._notebook.get_current_page()

        if num == 0:

            # Update general information

            if not pkg:
                self._info.status.set_text("")
                self._info.group.set_text("")
                self._info.installedsize.set_text("")
                self._info.priority.set_text("")
                self._info.channels.set_text("")
                return

            group = None
            installedsize = None
            channels = []
            for loader in pkg.loaders:
                info = loader.getInfo(pkg)
                if group is None:
                    group = info.getGroup()
                if installedsize is None:
                    installedsize = info.getInstalledSize()
                channel = loader.getChannel()
                channels.append("%s (%s)" %
                                (channel.getName() or channel.getAlias(),
                                 channel.getAlias()))

            flags = pkgconf.testAllFlags(pkg)
            if flags:
                flags.sort()
                flags = " (%s)" % ", ".join(flags)
            else:
                flags = ""

            status = pkg.installed and _("Installed") or _("Available")
            self._info.status.set_text(status+flags)
            self._info.group.set_text(group or _("Unknown"))
            self._info.priority.set_text(str(pkg.getPriority()))
            self._info.channels.set_text("\n".join(channels))

            if installedsize:
                self._info.installedsize.set_text(sizeToStr(installedsize))
                self._info.installedsize.show()
                self._info.installedsize_label.show()
            else:
                self._info.installedsize.hide()
                self._info.installedsize_label.hide()

        elif num == 1:

            # Update summary/description

            descrbuf = self._descrtv.get_buffer()
            descrbuf.set_text("")
            if not pkg: return

            iter = descrbuf.get_end_iter()
            for loader in pkg.loaders:
                info = loader.getInfo(pkg)
                summary = info.getSummary()
                if summary:
                    descrbuf.insert_with_tags_by_name(iter, summary+"\n\n",
                                                      "summary")
                    description = info.getDescription()
                    if description != summary:
                        descrbuf.insert_with_tags_by_name(iter,
                                                          description+"\n\n",
                                                          "description")
                    break
            else:
                loader = pkg.loaders.keys()[0]

        elif num == 2:

            # Update contents

            contbuf = self._conttv.get_buffer()
            contbuf.set_text("")
            if not pkg: return

            iter = contbuf.get_end_iter()
            for loader in pkg.loaders:
                if loader.getInstalled():
                    break
            else:
                loader = pkg.loaders.keys()[0]
            info = loader.getInfo(pkg)
            pathlist = info.getPathList()
            pathlist.sort()
            for path in pathlist:
                contbuf.insert_with_tags_by_name(iter, path+"\n", "content")

        elif num == 3:

            # Update relations

            if not pkg:
                self._relations.setPackages([])
                return

            self._setRelations(pkg)

        elif num == 4:

            # Update URLs

            model = self._urls.get_model()
            model.clear()

            if not pkg:
                return

            items = []
            for loader in pkg.loaders:
                channel = loader.getChannel()
                alias = channel.getAlias()
                info = loader.getInfo(pkg)
                for url in info.getURLs():
                    items.append((alias, sizeToStr(info.getSize(url)), url))

            items.sort()

            lastitem = None
            for item in items:
                if item != lastitem:
                    lastitem = item
                    model.append(item)

        elif num == 5:

            # Update reference

            refbuf = self._reftv.get_buffer()
            refbuf.set_text("")
            if not pkg: return

            iter = refbuf.get_end_iter()
            for loader in pkg.loaders:
                if loader.getInstalled():
                    break
            else:
                loader = pkg.loaders.keys()[0]
            info = loader.getInfo(pkg)
            urls = info.getReferenceURLs()
            for url in urls:
                tag = refbuf.create_tag(None,
                    foreground="blue", underline=pango.UNDERLINE_SINGLE)
                tag.set_data("url", url)
                refbuf.insert_with_tags(iter, url+"\n", tag)

    def _setRelations(self, pkg):

        class Sorter(str):
            ORDER = [_("Provides"), _("Upgrades"),
                     _("Requires"), _("Conflicts")]
            def __cmp__(self, other):
                return cmp(self.ORDER.index(str(self)),
                           self.ORDER.index(str(other)))
            def __lt__(self, other):
                return cmp(self, other) < 0

        relations = {}

        for prv in pkg.provides:

            prvmap = {}
            
            requiredby = []
            for req in prv.requiredby:
                requiredby.extend(req.packages)
            if requiredby:
                prvmap[_("Required By")] = requiredby

            upgradedby = []
            for upg in prv.upgradedby:
                upgradedby.extend(upg.packages)
            if upgradedby:
                prvmap[_("Upgraded By")] = upgradedby

            conflictedby = []
            for cnf in prv.conflictedby:
                conflictedby.extend(cnf.packages)
            if conflictedby:
                prvmap[_("Conflicted By")] = conflictedby

            if prvmap:
                relations.setdefault(Sorter(_("Provides")), {})[str(prv)] = \
                                                                        prvmap

        requires = {}
        for req in pkg.requires:
            lst = requires.setdefault(str(req), [])
            for prv in req.providedby:
                lst.extend(prv.packages)
            lst[:] = dict.fromkeys(lst).keys()
        if requires:
            relations[Sorter(_("Requires"))] = requires

        upgrades = {}
        for upg in pkg.upgrades:
            lst = upgrades.setdefault(str(upg), [])
            for prv in upg.providedby:
                lst.extend(prv.packages)
            lst[:] = dict.fromkeys(lst).keys()
        if upgrades:
            relations[Sorter(_("Upgrades"))] = upgrades

        conflicts = {}
        for cnf in pkg.conflicts:
            lst = conflicts.setdefault(str(cnf), [])
            for prv in cnf.providedby:
                lst.extend(prv.packages)
            lst[:] = dict.fromkeys(lst).keys()
        if conflicts:
            relations[Sorter(_("Conflicts"))] = conflicts

        self._relations.setPackages(relations, self._changeset)

# XXX This is deprecated and must be removed in the future.
#     No replacement is needed.
gobject.type_register(GtkPackageInfo)

# vim:ts=4:sw=4:et
