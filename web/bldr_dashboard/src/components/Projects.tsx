import React, { useState, useEffect, useRef } from 'react';
import { 
  apiService, 
  Project, 
  ProjectCreate, 
  ProjectUpdate,
  ProjectFile,
  unwrap 
} from '../services/api';
import { 
  Button, 
  Input, 
  Modal, 
  Form, 
  message, 
  Card, 
  List, 
  Popconfirm,
  Space,
  Upload,
  Table,
  Tag,
  Tabs,
  Descriptions,
  Divider
} from 'antd';
import { 
  EditOutlined, 
  DeleteOutlined, 
  UploadOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  BarChartOutlined,
  FolderAddOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { TabPane } = Tabs;

const Projects: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectFiles, setProjectFiles] = useState<ProjectFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [fileList, setFileList] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const directoryInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getProjects();
      setProjects(data);
    } catch (err: any) {
      console.error('Error fetching projects:', err);
      setError(err.response?.data?.detail || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (values: ProjectCreate & { folderPath?: string }) => {
    try {
      // Separate folder path from project data
      const { folderPath, ...projectData } = values;
      
      // Create the project
      const res = await apiService.createProject(projectData);
      // apiService.createProject returns Project directly
      const newProject = res as unknown as Project;
      message.success('Project created successfully');
      
      // If folder path is provided, automatically scan and attach files
      if (folderPath && newProject?.id) {
        try {
          message.loading(`Сканирование папки ${folderPath}...`, 0);
          
          // Use the backend's directory scanning functionality
          const result = await apiService.scanDirectoryForProject(newProject.id, folderPath);
          message.destroy();
          message.success(`${result.added} файлов из папки просканировано и добавлено успешно`);
        } catch (scanErr: any) {
          message.destroy();
          console.error('Ошибка сканирования папки:', scanErr);
          message.error(scanErr.response?.data?.detail || 'Не удалось просканировать папку');
        }
      }
      
      setIsModalVisible(false);
      form.resetFields();
      fetchProjects(); // Refresh the list
    } catch (err: any) {
      console.error('Error creating project:', err);
      message.error(err.response?.data?.detail || 'Failed to create project');
    }
  };

  const handleUpdateProject = async (values: ProjectUpdate) => {
    if (!editingProject) return;
    
    try {
      const res = await apiService.updateProject(editingProject.id, values);
      const { ok, error } = unwrap<any>(res);
      if (!ok) throw new Error(String(error));
      message.success('Project updated successfully');
      setIsEditModalVisible(false);
      editForm.resetFields();
      setEditingProject(null);
      fetchProjects(); // Refresh the list
    } catch (err: any) {
      console.error('Error updating project:', err);
      message.error(err.response?.data?.detail || 'Failed to update project');
    }
  };

  const handleDeleteProject = async (id: string) => {
    try {
      const res = await apiService.deleteProject(id);
      const { ok, error } = unwrap<any>(res);
      if (!ok) throw new Error(String(error));
      message.success('Project deleted successfully');
      fetchProjects(); // Refresh the list
    } catch (err: any) {
      console.error('Error deleting project:', err);
      message.error(err.response?.data?.detail || 'Failed to delete project');
    }
  };

  const showModal = () => {
    setIsModalVisible(true);
  };

  const showEditModal = (project: Project) => {
    setEditingProject(project);
    setIsEditModalVisible(true);
    editForm.setFieldsValue({
      name: project.name,
      code: project.code,
      location: project.location,
      status: project.status
    });
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
  };

  const handleEditCancel = () => {
    setIsEditModalVisible(false);
    editForm.resetFields();
    setEditingProject(null);
  };

  const handleProjectSelect = async (project: Project) => {
    setSelectedProject(project);
    try {
      setFilesLoading(true);
      const files = await apiService.getProjectFiles(project.id);
      setProjectFiles(files);
    } catch (err: any) {
      console.error('Error fetching project files:', err);
      message.error(err.response?.data?.detail || 'Failed to load project files');
    } finally {
      setFilesLoading(false);
    }
  };

  const handleAttachFiles = async () => {
    if (!selectedProject || fileList.length === 0) return;
    
    try {
      const files = fileList.map(file => file.originFileObj || file);
      const res = await apiService.addProjectFiles(selectedProject.id, files);
      const { ok, error } = unwrap<any>(res);
      if (!ok) throw new Error(String(error));
      message.success(`${files.length} files attached successfully`);
      
      // Refresh files list
      const filesData = await apiService.getProjectFiles(selectedProject.id);
      setProjectFiles(filesData);
      setFileList([]); // Clear the file list
      
      // Refresh projects list to update files count
      fetchProjects();
    } catch (err: any) {
      console.error('Error attaching files:', err);
      message.error(err.response?.data?.detail || 'Failed to attach files');
    }
  };

  const handleScanProject = async () => {
    if (!selectedProject) return;
    
    try {
      const result = await apiService.scanProjectFiles(selectedProject.id);
      const { ok, data, error } = unwrap<any>(result);
      if (!ok) throw new Error(String(error));
      message.success(`Scan completed: ${data.files_count} files, ${data.smeta_count} estimates, ${data.rd_count} RD files`);
      
      // Refresh files list
      const filesData = await apiService.getProjectFiles(selectedProject.id);
      setProjectFiles(filesData);
    } catch (err: any) {
      console.error('Error scanning project:', err);
      message.error(err.response?.data?.detail || 'Failed to scan project');
    }
  };

  const handleDirectorySelect = async () => {
    if (!selectedProject) return;
    
    try {
      // Prompt user for directory path
      const directoryPath = prompt('Введите путь к папке с файлами проекта:');
      
      if (directoryPath) {
        message.loading(`Сканирование папки ${directoryPath}...`, 0);
        
        try {
          // Use the backend's directory scanning functionality
          const result = await apiService.scanDirectoryForProject(selectedProject.id, directoryPath);
          message.destroy();
          message.success(`${result.added} файлов из папки просканировано и добавлено успешно`);
          
          // Refresh files list
          const filesData = await apiService.getProjectFiles(selectedProject.id);
          setProjectFiles(filesData);
          
          // Refresh projects list to update files count
          fetchProjects();
        } catch (err: any) {
          message.destroy();
          console.error('Ошибка сканирования папки:', err);
          message.error(err.response?.data?.detail || 'Не удалось просканировать папку');
        }
      }
    } catch (err: any) {
      console.error('Ошибка выбора папки:', err);
      message.error(err.response?.data?.detail || 'Не удалось выбрать папку');
    }
  };

  const uploadProps: UploadProps = {
    onRemove: (file) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file) => {
      setFileList([...fileList, file]);
      return false;
    },
    fileList,
    multiple: true,
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'smeta': return <FileTextOutlined />;
      case 'rd': return <FileTextOutlined />;
      case 'graphs': return <BarChartOutlined />;
      default: return <FileTextOutlined />;
    }
  };

  const getFileTagColor = (type: string) => {
    switch (type) {
      case 'smeta': return 'blue';
      case 'rd': return 'green';
      case 'graphs': return 'purple';
      default: return 'gray';
    }
  };

  if (loading) return <div>Загрузка проектов...</div>;
  if (error) return <div style={{ color: 'red' }}>Ошибка: {error}</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Проекты</h2>
        <Button type="primary" onClick={showModal}>
          Создать проект
        </Button>
      </div>
      
      {projects.length === 0 ? (
        <Card>
          <p>Нет проектов. Создайте новый!</p>
          <Button type="primary" onClick={showModal}>
            Создать проект
          </Button>
        </Card>
      ) : !selectedProject ? (
        <>
          <List
            grid={{ gutter: 16, column: 3 }}
            dataSource={projects}
            renderItem={project => (
              <List.Item>
                <Card 
                  title={project.name} 
                  extra={
                    <Space size="small">
                      <Button 
                        type="link" 
                        icon={<EditOutlined />} 
                        onClick={() => showEditModal(project)}
                        data-cy="edit-project"
                      />
                      <Popconfirm
                        title="Удалить проект?"
                        description="Все файлы проекта будут удалены"
                        onConfirm={() => handleDeleteProject(project.id)}
                        okText="Да"
                        cancelText="Нет"
                      >
                        <Button 
                          type="link" 
                          danger 
                          icon={<DeleteOutlined />} 
                          data-cy="delete-project"
                        />
                      </Popconfirm>
                    </Space>
                  }
                >
                  <p><strong>Код:</strong> {project.code}</p>
                  <p><strong>Статус:</strong> {project.status}</p>
                  <p><strong>Файлы:</strong> {project.files_count}</p>
                  <Button 
                    type="primary" 
                    onClick={() => handleProjectSelect(project)}
                    icon={<FolderOpenOutlined />}
                  >
                    Открыть проект
                  </Button>
                </Card>
              </List.Item>
            )}
          />
        </>
      ) : (
        <Card 
          title={selectedProject.name}
          extra={
            <Button onClick={() => setSelectedProject(null)}>
              Назад к списку
            </Button>
          }
        >
          <Tabs defaultActiveKey="details">
            <TabPane tab="Детали" key="details">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="Название">{selectedProject.name}</Descriptions.Item>
                <Descriptions.Item label="Код">{selectedProject.code}</Descriptions.Item>
                <Descriptions.Item label="Местоположение">{selectedProject.location}</Descriptions.Item>
                <Descriptions.Item label="Статус">{selectedProject.status}</Descriptions.Item>
                <Descriptions.Item label="Файлов">{selectedProject.files_count}</Descriptions.Item>
                <Descriptions.Item label="ROI">{selectedProject.roi}%</Descriptions.Item>
              </Descriptions>
              
              <div style={{ marginTop: 20 }}>
                <Button onClick={() => showEditModal(selectedProject)}>
                  Редактировать проект
                </Button>
              </div>
            </TabPane>
            
            <TabPane tab="Файлы" key="files">
              <div style={{ marginBottom: 20 }}>
                <Upload {...uploadProps}>
                  <Button icon={<UploadOutlined />}>Выбрать файлы</Button>
                </Upload>
                <div style={{ marginTop: 10 }}>
                  <Button 
                    type="primary" 
                    onClick={handleAttachFiles}
                    disabled={fileList.length === 0}
                  >
                    Прикрепить {fileList.length > 0 ? `(${fileList.length})` : ''} файлов
                  </Button>
                  <Button 
                    style={{ marginLeft: 10 }}
                    icon={<FolderAddOutlined />}
                    onClick={handleDirectorySelect}
                  >
                    Прикрепить папку
                  </Button>
                  <Button 
                    style={{ marginLeft: 10 }}
                    onClick={handleScanProject}
                  >
                    Сканировать проект
                  </Button>
                </div>
              </div>
              
              <Table
                loading={filesLoading}
                dataSource={projectFiles}
                columns={[
                  {
                    title: 'Имя',
                    dataIndex: 'name',
                    key: 'name',
                  },
                  {
                    title: 'Тип',
                    dataIndex: 'type',
                    key: 'type',
                    render: (type: string) => (
                      <Tag icon={getFileIcon(type)} color={getFileTagColor(type)}>
                        {type}
                      </Tag>
                    ),
                  },
                  {
                    title: 'Размер',
                    dataIndex: 'size',
                    key: 'size',
                    render: (size: number) => `${(size / 1024).toFixed(1)} KB`,
                  },
                  {
                    title: 'Дата загрузки',
                    dataIndex: 'uploaded_at',
                    key: 'uploaded_at',
                  },
                ]}
                pagination={{ pageSize: 10 }}
              />
            </TabPane>
          </Tabs>
        </Card>
      )}

      {/* Create Project Modal */}
      <Modal
        title="Создать новый проект"
        visible={isModalVisible}
        onCancel={handleCancel}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateProject}
        >
          <Form.Item
            name="name"
            label="Название проекта"
            rules={[{ required: true, message: 'Введите название проекта' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="code"
            label="Код проекта"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="location"
            label="Местоположение"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="Статус"
          >
            <Input defaultValue="planned" />
          </Form.Item>
          
          <Form.Item
            name="folderPath"
            label="Путь к папке с файлами проекта (опционально)"
          >
            <Input placeholder="C:\path\to\project\folder" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit">
              Создать проект
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Project Modal */}
      <Modal
        title="Редактировать проект"
        visible={isEditModalVisible}
        onCancel={handleEditCancel}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateProject}
        >
          <Form.Item
            name="name"
            label="Название проекта"
            rules={[{ required: true, message: 'Введите название проекта' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="code"
            label="Код проекта"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="location"
            label="Местоположение"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="Статус"
          >
            <Input />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit">
              Обновить проект
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Projects;