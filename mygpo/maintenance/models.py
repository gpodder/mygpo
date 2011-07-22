from couchdbkit.ext.django.schema import *

class CommandRunStatus(DocumentSchema):
    """ Status of a single Command run """

    timestamp_started  = DateTimeProperty()
    timestamp_finished = DateTimeProperty()
    error_msg          = StringProperty()
    start_seq          = IntegerProperty()
    end_seq            = IntegerProperty()
    status_counter     = DictProperty()

    def __repr__(self):
        return '<%(cls)s %(start_seq)d - %(end_seq)d>' % \
            dict(cls=self.__class__.__name__, start_seq=self.start_seq,
                 end_seq=self.end_seq)


class CommandStatus(Document):
    """ Contains status info for several runs of a command """

    command            = StringProperty()
    runs               = SchemaListProperty(CommandRunStatus)


    @property
    def last_seq(self):
        runs = filter(lambda r: r.end_seq, self.runs)
        return runs[-1].end_seq if runs else 0


    def __repr__(self):
        return '<%(cls)s %(cmd)s %(num_runs)d>' % \
            dict(cls=self.__class__.__name__, cmd=self.command,
                 num_runs=len(self.runs))
