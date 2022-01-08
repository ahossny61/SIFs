using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using MySql.Data.MySqlClient;
using System.Diagnostics;
using WindowsFormsApplication2;

namespace SIFsDesign
{

    public partial class mainForm : Form
    {
        int counter =0;
      
        List<data> items = new List<data>();
        string connectionString;
        MySqlConnection connection;
        String query;
        MySqlDataReader reader;
        MySqlCommand cmd=new MySqlCommand();
       

        float end =0;
        string[] Labels = { "person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck",
              "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
              "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
              "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
              "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
              "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
              "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
              "chair", "sofa", "pottedplant", "bed", "diningtable", "toilet", "tvmonitor", "laptop", "mouse",
              "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
              "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush" };
        public mainForm()
        {
            InitializeComponent();
        }

        private void mainForm_Load(object sender, EventArgs e)
        {
            
            connectionString = "SERVER= localhost;DATABASE= graduation;UID= root;PASSWORD=ahmed19234";
            connection = new MySqlConnection(connectionString);
            listBox1.HorizontalScrollbar = true;
            result.AutoCompleteMode = AutoCompleteMode.SuggestAppend;
            result.AutoCompleteSource = AutoCompleteSource.CustomSource;
            AutoCompleteStringCollection collection = new AutoCompleteStringCollection();
            collection.AddRange(Labels);
            result.AutoCompleteCustomSource = collection;
        }
        ~mainForm(){
            Form1 f1 = new Form1();
            f1.Close();
            Application.Exit();
         }




        //Play button Click event
        private void button3_Click(object sender, EventArgs e)
        {
            int i = listBox1.SelectedIndex;
            if (i >= 0)
            {
              
                string path = items[i].path;
                if (File.Exists(path))
                {
                    wmp2.URL = path;
                    end = items[i].end;
                    
                    wmp2.Ctlcontrols.currentPosition = items[i].start;
                    
                    
                }
                else MessageBox.Show("Select Video!");
            }
            else MessageBox.Show("SELECT VIDEO!");
        }

        private void pausebtn_Click(object sender, EventArgs e)
        {
            wmp2.Ctlcontrols.pause();
        }

        private void button1_Click(object sender, EventArgs e)
        {

        }

        private void mainForm_FormClosing(object sender, FormClosingEventArgs e)
        {

         
        }

       
        // btn search click event
        private void button1_Click_1(object sender, EventArgs e)
        {
            listBox1.Items.Clear();
            items.Clear();
            counter = 0;
            String search_result = result.Text;
            if (Labels.Contains(search_result))
            {

                try
                {
                    connection.Open();
                    query = "select * from objects where object = '"+search_result+"'";
                    cmd.Connection = connection;
                    cmd.CommandText = query;
                    reader = cmd.ExecuteReader();
                    while (reader.Read())
                    {
                        items.Add(new data(reader["name"].ToString(),reader["path"].ToString(), reader["object"].ToString(),float.Parse(reader["start"].ToString()),float.Parse( reader["end"].ToString())));
                        int start = (int)(items[counter].start);
                        int end = (int)(items[counter].end);
                        TimeSpan t_start = TimeSpan.FromSeconds(start);
                        string start_format = string.Format("{0:D2}h:{1:D2}m:{2:D2}s", t_start.Hours, t_start.Minutes, t_start.Seconds);
                        TimeSpan t_end = TimeSpan.FromSeconds(end);
                        string end_format = string.Format("{0:D2}h:{1:D2}m:{2:D2}s", t_end.Hours, t_end.Minutes, t_end.Seconds);
                        listBox1.Items.Add(" "+items[counter].name+"\t"+start_format+"\t"+end_format);
                        counter++;
                    }
                    connection.Close();
                }
                catch(Exception ex)
                {
                    
                    MessageBox.Show(ex.Message);
                }

                if (items.Count == 0)
                {
                    MessageBox.Show("Not found in our videos .Please ,make sure from the name");
                }

            }
            else
            {
                MessageBox.Show("not in our labels ");
            }

           
        }

        private void listBox1_SelectedIndexChanged(object sender, EventArgs e)
        {

        }

        private void textBox1_TextChanged(object sender, EventArgs e)
        {
           
        }

        private void panel2_Paint(object sender, PaintEventArgs e)
        {

        }

        private void panel3_Paint(object sender, PaintEventArgs e)
        {

        }

        private void button3_Click_1(object sender, EventArgs e)
        {
            Application.Exit();
        }

        private void panel3_Paint_1(object sender, PaintEventArgs e)
        {

        }
    }
}
