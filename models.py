from wsgic.database.columns import *
from wsgic_auth.models import *

# db = SqliteDatabase(config.get("databases.sqlite.path", "database.sqlite"), config.get("databases.sqlite.debug", False), verbose=config.get("databases.sqlite.verbose", False), check_same_thread=False)

# @db.on('error')
# def etror(e):raise e

class ActivityCategory(database.Model):
    name: str
    icon_cls: str
    
    def __str__(self):
        return f"[{self.id}] {self.name}"

class Activity(database.Model):
    title: str
    date: datetime = DateTimeColumn()
    user: int = ForeignKeyColumn(User)
    category: str = ForeignKeyColumn(ActivityCategory)
    body: str = RichTextColumn(helper_text="Activity description")

    @classmethod
    def count_monthly(self, month):
        return len(list(filter(lambda x: x.date.month == month, self.objects.get())))

# Activity.objects.delete(title="User Login")

def trigger_activity(title, body, category="System"):
    category = ActivityCategory.objects.get(name=category)
    Activity.objects.create(title=title, body=body, date=datetime.now(), category=category[0], user=request.user)