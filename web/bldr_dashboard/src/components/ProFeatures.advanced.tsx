import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Upload, 
  Tabs, 
  Table, 
  message, 
  Spin, 
  Select, 
  Row, 
  Col,
  Divider,
  Descriptions,
  Tag,
  UploadProps,
  Modal,
  Progress,
  Statistic,
  List,
  Typography,
  Switch,
  DatePicker,
  Space,
  Slider
} from 'antd';
import { UploadOutlined, FilePdfOutlined, FileExcelOutlined, DownloadOutlined, FileImageOutlined, PlusOutlined, SyncOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, FolderOpenOutlined } from '@ant-design/icons';
import type { UploadProps as AntdUploadProps } from 'antd';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { apiService, LetterData, BudgetData, PPRData, TenderData, LetterResponse, BudgetResponse, PPRResponse, TenderResponse, Project, Template } from '../services/api';
import { useStore } from '../store';

const { TabPane } = Tabs;
const { Option } = Select;

const ProFeatures: React.FC = () => {
  const [activeTab, setActiveTab] = useState('letters');
  const [loading, setLoading] = useState(false);
  const [letterForm] = Form.useForm();
  const [budgetForm] = Form.useForm();
  const [pprForm] = Form.useForm();
  const [tenderForm] = Form.useForm();
  const [bimForm] = Form.useForm();
  const [dwgForm] = Form.useForm();
  const [monteCarloForm] = Form.useForm();
  // New state for batch estimate parsing
  const [estimateForm] = Form.useForm();
  const [estimateFileList, setEstimateFileList] = useState<any[]>([]);
  const [batchEstimateResults, setBatchEstimateResults] = useState<any>(null);
  const [isBatchModalVisible, setIsBatchModalVisible] = useState(false);
  
  // New state for norms management
  const [normsStatus, setNormsStatus] = useState<any>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateResults, setUpdateResults] = useState<any>(null);
  const [cronEnabled, setCronEnabled] = useState(true);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  
  // New state for norms list
  const [normsData, setNormsData] = useState<any[]>([]);
  const [normsLoading, setNormsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actualCount, setActualCount] = useState(0);
  const [outdatedCount, setOutdatedCount] = useState(0);
  const [updating, setUpdating] = useState(false);

  // Project integration state
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [projectFiles, setProjectFiles] = useState<any[]>([]);
  const [isProjectLoading, setIsProjectLoading] = useState(false);

  return (
    <div>
      <h2>Pro Features</h2>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Letters" key="letters">
          <Card title="Official Letters">
            <p>Letter generation functionality</p>
          </Card>
        </TabPane>
        <TabPane tab="Budget" key="budget">
          <Card title="Auto Budget">
            <p>Budget calculation functionality</p>
          </Card>
        </TabPane>
        <TabPane tab="PPR" key="ppr">
          <Card title="PPR Generation">
            <p>PPR generation functionality</p>
          </Card>
        </TabPane>
        <TabPane tab="Tender" key="tender">
          <Card title="Tender Analysis">
            <p>Tender analysis functionality</p>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default ProFeatures;