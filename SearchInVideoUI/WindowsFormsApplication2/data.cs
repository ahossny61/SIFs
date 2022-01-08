using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WindowsFormsApplication2
{
    public class data
    {
        public string name, path, obj;
        public float start, end;

        public data(string name, string path, string obj, float start, float end)
        {
            this.name = name;
            this.path = path;
            this.obj = obj;
            this.start = start;
            this.end = end;
        }
    }
}
