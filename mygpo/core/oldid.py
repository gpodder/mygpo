from couchdbkit.ext.django.schema import *


class OldIdMixin(DocumentSchema):
    """ Objects that have an Old-Id from the old MySQL backend """

    oldid = IntegerProperty()
    merged_oldids = ListProperty()


    def set_oldid(self, oldid):
        if self.oldid:
            self.add_merged_oldid(self.oldid)
        self.oldid = oldid


    def add_merged_oldid(self, oldid):
        if oldid not in self.merged_oldids:
            self.merged_oldids.append(oldid)
